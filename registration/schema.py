import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.fields import DjangoConnectionField
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.rest_framework.mutation import SerializerMutation
from .models import Event, Booking, Discipline, Document, Day, Rate, Price, Product, ProductVariant
from rest_framework import serializers
from graphene import relay
from graphql_relay import from_global_id, to_global_id


class ProductType(DjangoObjectType):
    class Meta:
        fields = ["name", "kind", "variants"]
        model = Product
        interfaces = [relay.Node]


class ProductVariantType(DjangoObjectType):
    class Meta:
        fields = ["name", "price"]
        model = ProductVariant
        interfaces = [relay.Node]


class PriceType(DjangoObjectType):
    class Meta:
        fields = ["valid_from", "valid_until", "price_day", "price"]
        model = Price
        interfaces = [relay.Node]


class RateType(DjangoObjectType):
    class Meta:
        fields = ["id", "label", "dob_from", "dob_to", "non_rider", "prices", "disciplines"]
        model = Rate
        interfaces = [relay.Node]
        filter_fields = {
            "dob_from": ["lte"],
            "dob_to": ["gte"],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(is_active=True)


class DayType(DjangoObjectType):
    class Meta:
        fields = ["id", "day"]
        model = Day
        interfaces = [relay.Node]


class DisciplineType(DjangoObjectType):
    class Meta:
        fields = ("id", "label", "code")
        model = Discipline
        interfaces = [relay.Node]


class DocumentType(DjangoObjectType):
    class Meta:
        model = Document
        fields = ["id", "name", "document"]
        interfaces = [relay.Node]

    @staticmethod
    def resolve_document(instance, info):
        return instance.document.url


class EventType(DjangoObjectType):
    """A sports event like a competition or a convention"""
    arrival = graphene.List(DayType)
    departure = graphene.List(DayType)
    rates_available = graphene.List(RateType)

    @staticmethod
    def resolve_logo(event, info):
        return event.logo.url

    @staticmethod
    def resolve_arrival(event, info):
        return event.arrival

    @staticmethod
    def resolve_departure(event, info):
        return event.departure

    @staticmethod
    def resolve_rates_available(event, info):
        return grapevent.rates.filter(is_active=True)

    class Meta:
        model = Event
        fields = ("id", "slug", "begin_date", "end_date", "name", "host", "description", "logo", "sex_is_required",
                  "address_is_required", "phone_is_required", "disciplines", "documents",
                  "arrival", "departure", "rates", "food_is_included", "vegan", "vegetarian",
                  "vegan_breakfast_only", "products",
                  "is_open")
        interfaces = [relay.Node]


class BookingSerializer(serializers.ModelSerializer):
    disciplines = serializers.PrimaryKeyRelatedField(many=True, queryset=Discipline.objects.all(), required=False)

    class Meta:
        model = Booking
        fields = ("disciplines", "event", "code", "date_of_birth", "email",  "last_name",
                  "club", "first_name", "notes", "address", "zipcode", "city",  "phone",
                  "arrival", "departure", "rate")
        convert_choices_to_enum = False


class BookingType(DjangoObjectType):
    class Meta:
        model = Booking
        fields = ("id", "disciplines", "event", "code", "date_of_birth", "email", "food", "last_name", "package",
                  "club", "first_name", "sex", "notes", "address", "zipcode", "city", "country", "phone", "arrival", "departure", "rate")
        interfaces = [relay.Node]

class BookingCreateMutation(SerializerMutation):
    class Meta:
        serializer_class = BookingSerializer
        model_operations = ["create"]

class Query(graphene.ObjectType):
    """Uniconvention.com GraphQL endpoint"""
    all_events = DjangoConnectionField(EventType)
    all_bookings = graphene.List(BookingType)
    event = graphene.Field(EventType, id=graphene.Int())

    def resolve_all_events(self, info, **kwargs):
        return Event.objects.all()

    def resolve_all_bookings(self, info, **kwargs):
        return Booking.objects.all()

    def resolve_event(self, info, **kwargs):
        id = kwargs.get("id")
        if id is not None:
            return Event.objects.get(id=id)
        return None

class Mutation(graphene.ObjectType):
    create_booking = BookingCreateMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)