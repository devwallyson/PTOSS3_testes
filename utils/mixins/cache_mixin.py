from django.core.cache import cache
from django.utils.cache import add_never_cache_headers
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.views.decorators.cache import cache_page


class CachedViewSetMixin:
    cache_key_prefix = None
    cache_timeout = 600 * 6

    @classmethod
    def get_cache_key_prefix_from_path(cls, viewset_path):
        try:
            if isinstance(viewset_path, str):
                viewset_class = import_string(viewset_path)
                return viewset_class.cache_key_prefix
            return viewset_path.cache_key_prefix
        except (ImportError, AttributeError) as e:
            print(f"Error getting cache key prefix for {viewset_path}: {str(e)}")  # TODO: usar logger[ERROR] em prod
            return None

    def get_cache_key_prefix(self):
        if self.cache_key_prefix is None:
            raise NotImplementedError("cache_key_prefix must be set in the ViewSet")
        return self.cache_key_prefix

    def delete_view_cache(self):
        keys_pattern = f"*.{self.cache_key_prefix}.*"
        cache.delete_pattern(keys_pattern)
        print(f"Cache invalidated for prefix: {self.cache_key_prefix}", flush=True)  # TODO: usar logger[INFO] em prod

    def delete_multiple_view_cache(self, viewset_paths):
        for path in viewset_paths:
            prefix = self.get_cache_key_prefix_from_path(path)
            if prefix:
                keys_pattern = f"*.{prefix}.*"
                cache.delete_pattern(keys_pattern)
                print(f"Cache invalidated for prefix: {prefix}")  # TODO: usar logger[INFO] em prod
            else:
                print(f"Could not invalidate cache for path: {path}")  # TODO: usar logger[warning/error] prod

    def delete_related_view_cache(self, additional_viewsets=None):
        viewsets_to_invalidate = getattr(self, "related_viewsets", [])
        if additional_viewsets:
            viewsets_to_invalidate.extend(additional_viewsets)
        self.delete_multiple_view_cache(viewsets_to_invalidate)

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        add_never_cache_headers(response)
        return response

    @method_decorator(cache_page(cache_timeout))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.delete_view_cache()
        return response

    def perform_create(self, serializer):
        response = super().perform_create(serializer)
        self.delete_view_cache()
        return response

    @method_decorator(cache_page(cache_timeout))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self.delete_view_cache()
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        self.delete_view_cache()
        return response

    def perform_update(self, serializer):
        response = super().perform_update(serializer)
        self.delete_view_cache()
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        self.delete_view_cache()
        return response

    def perform_destroy(self, instance):
        response = super().perform_destroy(instance)
        self.delete_view_cache()
        return response
