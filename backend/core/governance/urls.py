from django.urls import path
from core.governance.api_exploration import (
    ProductListView, ProductDetailView, ProductReleasesView,
    ReleaseListView, ReleaseDetailView, ReleaseObservationsView,
    ReleaseLineageView, TriggerPopulationTransformationView,
)

urlpatterns = [
    path('data-products/', ProductListView.as_view(), name='data-products'),
    path('data-products/<slug:code>/', ProductDetailView.as_view(), name='data-product-detail'),
    path('data-products/<slug:code>/releases/', ProductReleasesView.as_view(), name='data-product-releases'),
    path('data-products/<slug:code>/transform/', TriggerPopulationTransformationView.as_view(), name='population-transform'),
    path('data-product-releases/', ReleaseListView.as_view(), name='data-product-releases-list'),
    path('data-product-releases/<uuid:id>/', ReleaseDetailView.as_view(), name='data-product-release-detail'),
    path('data-product-releases/<uuid:release_id>/observations/', ReleaseObservationsView.as_view(), name='release-observations'),
    path('data-product-releases/<uuid:release_id>/lineage/', ReleaseLineageView.as_view(), name='release-lineage'),
]
