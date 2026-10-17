
from rest_framework.pagination import PageNumberPagination


class AcquisitionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class AcquisitionObservationPagination(
    PageNumberPagination
):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
