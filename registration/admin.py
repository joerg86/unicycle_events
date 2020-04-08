# +-+ coding: utf-8 +-+

from django.contrib import admin

from registration.models import Booking, Transaction, Event, WebPage, Day, Document, Attachment, Rate, Discipline, Price, \
    Product, ProductVariant

from django.db.models import Sum, Count, F, When, Case, IntegerField
from django.db.models.functions import Coalesce
from django.utils.html import format_html
from django.utils import timezone
from import_export import resources
from import_export.admin import ExportMixin
from import_export.fields import Field
from django.template import defaultfilters
from django.utils.translation import gettext_lazy as _

# Register your models here.


class TransactionInline(admin.TabularInline):
    model = Transaction


class TagInline(admin.TabularInline):
    model = Day


class DisciplineInline(admin.TabularInline):
    model = Discipline


class RateInline(admin.TabularInline):
    model = Rate


class DocumentInline(admin.TabularInline):
    model = Document


class AttachmentInline(admin.TabularInline):
    model = Attachment


class PreisInline(admin.TabularInline):
    model = Price


def checkin(modeladmin, request, queryset):
    for b in queryset:
        b.checkin = timezone.now()
        b.save()


checkin.short_description = "Einchecken" 


class BookingResource(resources.ModelResource):
    class Meta:
        model = Booking
    
    def dehydrate_paket(self, booking):
        return str(booking.paket)

    def dehydrate_anreise(self, booking):
        return str(booking.anreise)

    def dehydrate_abreise(self, booking):
        return str(booking.abreise)

    def dehydrate_rate(self, booking):
        return str(booking.rate)

    def dehydrate_food(self, booking):
        return booking.get_food_display()

    def dehydrate_disciplines(self, booking):
        return ", ".join(map(lambda x: x.code, booking.disciplines.all()))


class RateAdmin(admin.ModelAdmin):
    list_display = ["label", "event", "dob_from", "dob_to", "non_rider"]

    inlines = [PreisInline]


class BookingAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("event", "date_short", "code", "last_name", "first_name", 
                    "date_of_birth", "age", "club", "food", "show_paid", "show_open", "colored_state",
                    "checkin_date")

    list_filter = ("event", "checkin_date", "state", "food", "club")
    search_fields = ("first_name", "last_name", "club", "code")
    list_display_links = ["code"]
    actions = [checkin]
    csv_fields = ("last_name", "first_name", "club", "code")
    resource_class = BookingResource

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if not request.user.is_superuser:
            if db_field.name == "event":
                kwargs["queryset"] = Event.objects.filter(admin=request.user)
            if db_field.name == "schlafen":
                kwargs["queryset"] = Sleep.objects.filter(packages__event__admin=request.user).distinct()

        return super(BookingAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def age(self, obj):
        color = "green" if obj.full_age() else "red"
        return format_html("<span style='color: {}'>{}</span>", color, obj.age().years)

    age.admin_order_field = "date_of_birth"
    age.short_description = _("age")

    def date_short(self, obj):
        return format_html(defaultfilters.date(timezone.localtime(obj.date), "SHORT_DATETIME_FORMAT"))
    date_short.admin_order_field = "date"
    date_short.short_description = _("date")

    fieldsets = (
        (None, {
            "fields": ["date", "code", "amount", "event"],
        }),
        (_("Personal data"), {
            "fields": [("first_name", "last_name", "sex"), ("email", "club"), "date_of_birth"],
        }),
        (_("Address and phone number"), {
            "fields": ["address", ("zipcode", "city"), "country", "phone"]
        }),
        (_("Participation details"), {
            "fields": [("arrival", "departure", "rate"), ("disciplines", )],
        }),
        (_("Workflow"), {
            "fields": [("notes", "internal_notes"), "state"]
        }),
    )

    readonly_fields = ["amount", "date"]

    def get_queryset(self, request):
        qs = Booking.objects.prefetch_related("transaction_set").annotate(paid=Sum('transaction__betrag'), open_amount=F("amount")-Sum("transaction__betrag"))
        if not request.user.is_superuser:
            return qs.filter(event__admin=request.user)
        return qs

    def colored_state(self, inst):
        color = "orange"
        if inst.state == "confirmed":
            color = "darkgreen"
        elif inst.state in ["problem", "canceled"]:
            color = "darkred"
        return format_html("<span style='color:{}'>{}</span>",color, inst.get_state_display())

    colored_state.short_description = "Status"
    colored_state.admin_order_field = "status"

    def show_paid(self, inst):
        return inst.paid or 0.0

    show_paid.admin_order_field = 'paid'
    show_paid.short_description = _("paid")

    def show_open(self, inst):
        if inst.open_amount is None:
            return inst.amount
        else:
            return inst.open_amount

    show_open.admin_order_field = 'offen'
    show_open.short_description = _("open")

    inlines = [ AttachmentInline, TransactionInline ]


class TransactionResource(resources.ModelResource):
    class Meta:
        model = Transaction

    def dehydrate_booking(self, trans):
        return str(trans.booking)


class TransactionAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("id", "datum", "typ", "mittel", "nr", "betrag", "gebuehr", "booking")
    list_filter = ("booking__event",  )
    list_select_related = ("booking",)
    resource_class = TransactionResource

    def get_queryset(self, request):
        qs = Transaction.objects.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(booking__event__admin=request.user)


class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "host","begin_date", "end_date")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (None, {
            "fields": ["name", "slug", "description", "logo", "is_open"]
        }),
        (_("Time & location"), {
            "fields": [("host", "begin_date", "end_date"),]
        }),
        (_("Booking form"), {
            "fields": ["address_is_required", "phone_is_required", "sex_is_required"] 
        }),
        (_("Food"), {
            "fields": ["food_is_included", "vegetarian", "vegan", "vegan_breakfast_only"]
        }),
        (_("Payment details"), {
            "fields": ["paypal", ("account_holder", "iban", "bic")]
        }),
        (_("Contact person"), {
            "fields": ["contact_name", "contact_email"]
        }),
        (_("Administration"), {
            "fields": ["admin"]
        })
    )

    inlines = [TagInline, DocumentInline, DisciplineInline]

    def save_model(self, request, obj, form, change):             
        if not change:
            obj.admin = request.user
        obj.save()

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ["admin"]
        return []

    def get_queryset(self, request):
        qs = super(EventAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(admin=request.user)


class WebPageAdmin(admin.ModelAdmin):
    list_display = ("event", "slug", "name", "icon", "order")

    def get_queryset(self, request):
        qs = WebPage.objects.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(event__admin=request.user)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant

class ProductAdmin(admin.ModelAdmin):
    list_display = ("kind", "name", "order", "event")
    inlines = [ProductVariantInline]

admin.site.register(Booking, BookingAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(WebPage, WebPageAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(Product, ProductAdmin)
