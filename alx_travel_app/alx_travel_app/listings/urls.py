from .views import ListingViewSet, BookingViewSet
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register('listings', ListingViewSet)
router.register('bookings', BookingViewSet)

urlpatterns = router.urls