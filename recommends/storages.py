from django.contrib.sites.models import Site
from .converters import resolve_identifier, get_identifier
from .models import SimilarityResult, Recommendation


class RecommendationStorage(object):
    def get_identifier(self, obj, *args, **kwargs):
        """Given an object and optional parameters, returns a string identifying the object uniquely"""
        raise NotImplementedError

    def resolve_identifier(self, identifier):
        """Returns an object corresponding to an identifier in the format returned by ``get_identifier``"""
        raise NotImplementedError

    def get_similarities_for_object(self, obj, limit):
        raise NotImplementedError

    def get_recommendations_for_user(self, user, limit):
        raise NotImplementedError

    def store_similarities(self, itemMatch):
        raise NotImplementedError

    def store_recommendations(self, recommendations):
        """
        ``recommendations`` is an iterable with the following schema::

            (
                (
                    <user>,
                    (
                        (<score>, <object_identifier>),
                        (<score>, <object_identifier>)
                    ),
                )
            )
        """
        raise NotImplementedError


class DjangoOrmStorage(RecommendationStorage):
    def get_identifier(self, obj, site=None, rating=None, *args, **kwargs):
        if rating is not None:
            site = self.get_rating_site(rating)
        if site is None:
            site = Site.objects.get_current()
        return get_identifier(obj, site)

    def resolve_identifier(self, identifier):
        return resolve_identifier(identifier)

    def get_similarities_for_object(self, obj, limit):
        object_site = Site.objects.get_current()
        return SimilarityResult.objects.similar_to(obj, site=object_site, score__gt=0).order_by('-score')[:limit]

    def get_recommendations_for_user(self, user, limit):
        object_site = Site.objects.get_current()
        return Recommendation.objects.filter(user=user, object_site=object_site).order_by('-score')[:limit]

    def store_similarities(self, itemMatch):
        for object_id, scores in itemMatch.items():
            for score, related_object_id in scores:
                object_target, object_target_site = self.resolve_identifier(object_id)
                object_related, object_related_site = self.resolve_identifier(related_object_id)
                SimilarityResult.objects.set_score_for_objects(
                    object_target=object_target,
                    object_target_site=object_target_site,
                    object_related=object_related,
                    object_related_site=object_related_site,
                    score=score
                )

    def store_recommendations(self, recommendations):
        for (user, rankings) in recommendations:
            for score, object_id in rankings:
                object_recommended, site = self.resolve_identifier(object_id)
                Recommendation.objects.set_score_for_object(
                    user=user,
                    object_recommended=object_recommended,
                    object_site=site,
                    score=score
                )
