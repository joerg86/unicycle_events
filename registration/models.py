# +-+ coding: utf-8 +-+
from django.db import models
import random
import string
from django.utils import timezone
from django.urls import reverse
from django.utils.http import urlencode
from localflavor.generic.models import IBANField, BICField
from ckeditor_uploader.fields import RichTextUploadingField
from django_countries.fields import CountryField
from datetime import date
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext_lazy as _

# Create your models here.

ESSEN_CHOICES = (
    ("all", _("all")),
    ("v", _("vegetarian")),
    ("vv", _("vegan")),
)

STATUS_CHOICES = (
    ("open", _("open")),
    ("progress", _("in progress")),
    ("confirmed", _("confirmed")),
    ("problem", _("problem")),
    ("canceled", _("canceled")),
)

GESCHLECHT_CHOICES = (
    ("f", _("female")),
    ("m", _("male")),
)


class Event(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(_("short name"), help_text=_("Short name for the URL, only use alphanumeric characters and dashes, e.g. 'arizona-muni-event-2021'"), unique=True)
    begin_date = models.DateTimeField(_("begin date"))
    end_date = models.DateTimeField(_("end date"))
    description = models.TextField(_("description"))
    logo = models.ImageField(_("logo"), upload_to="logos", blank=True, null=True)
    is_open = models.BooleanField(default=True, help_text=_("Registration is currently open"))

    contact_email = models.EmailField(_("e-mail contact"))
    contact_name = models.CharField(_("name"), max_length=100)
    host = models.CharField(help_text=_("name of the host"), max_length=100)

    paypal = models.EmailField(_("PayPal address"), help_text=_("Payments are sent to this address"), blank=True)
    account_holder = models.CharField(max_length=100, blank=True)
    bic = BICField(_("BIC"), blank=True)
    iban = IBANField(_("IBAN"), blank=True)

    address_is_required = models.BooleanField(
        _("address is required"), 
        help_text=_("Does the post address need to be entered upon registration?"), 
        default=False
    )
    
    phone_is_required = models.BooleanField(
        _("phone is required"), 
        help_text=_("Does an emergency phone number need to be provided upon registration?"), 
        default=False
    )

    sex_is_required  = models.BooleanField(
        _("sex is required"), 
        help_text=_("Does the sex need to be specified upon registration?"), 
        default=False
    )

    food_is_included = models.BooleanField(
        _("food is included"),
        help_text=_("Food is offered and included in the booking fee"), 
        default=True
    )
    
    vegetarian = models.BooleanField(
        _("vegetarian"), 
        help_text=_("Vegetarian meals can be selected"), 
        default=True
    )

    vegan = models.BooleanField(
        _("vegan"), 
        help_text=_("There's a vegan choice available"), 
        default=True
    )

    vegan_breakfast_only = models.BooleanField(
        _("Only vegan breakfast"), 
        help_text="Der Benutzer wird bei der Buchung darauf hingewiesen, dass nur das Frühstück vegan ist.", 
        default=False
    )

    admin = models.ForeignKey("auth.User", on_delete=models.CASCADE, help_text="Dieser Benutzer kann das Event verwalten")

    def get_absolute_url(self):
        return reverse("convention:seite", args=[self.slug])

    def __str__(self):
        return self.name

    @property
    def arrival(self):
        return self.days.filter(arrival=True)

    @property
    def departure(self):
        return self.days.filter(departure=True)

    @property
    def rates_available(self):
        return self.rates.filter(is_active=True)


    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ("-begin_date", "-end_date")  


class Rate(models.Model):
    event = models.ForeignKey("Event", related_name="rates", on_delete=models.CASCADE)
    label = models.CharField(max_length=100)

    dob_from = models.DateField(_("DOB from"), blank=True, null=True)
    dob_to = models.DateField(_("DOB to"), blank=True, null=True)

    non_rider = models.BooleanField(
        _("Companion rate"),
        help_text=_("This rate is intended for people who do not actively participate (e.g. coaches, companions of minors)"),
        default=False
    )

    disciplines = models.ManyToManyField(
        "Discipline",
        verbose_name=_("discipline"),
        help_text=_("Disciplines included in this rate - applies to all disciplines if left empty"),
        blank=True
    )

    is_active = models.BooleanField(
        _("Is active"),
        help_text=_("This rate can currently be booked"),
        default=True
    )

    order = models.PositiveIntegerField(_("ordering"), default=0)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ("order", "label")
        verbose_name = _("rate")
        verbose_name_plural = _("rates")


class Price(models.Model):
    rate = models.ForeignKey("Rate", on_delete=models.CASCADE, related_name="prices")
    valid_from = models.DateField(_("valid from"), null=True, blank=True)
    valid_until = models.DateField(_("valid until"), null=True, blank=True)

    price_day = models.DecimalField(_("price per day"), max_digits=8, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(_("total price"), max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ("valid_until",)
        verbose_name = _("price")
        verbose_name_plural = _("prices")


PRODUCT_KIND_CHOICES = (
    ("shirt", _("t-shirt")),
    ("accommodation", _("accommodation")),
    ('meal', _("meal")),
    ("other", _("other")),
)


class Product(models.Model):
    event = models.ForeignKey("Event", related_name="products", on_delete=models.CASCADE)
    kind = models.CharField(_("kind"), max_length=100, choices=PRODUCT_KIND_CHOICES)
    name = models.CharField(_("name"), max_length=100, blank=True)
    required = models.BooleanField(_("required"), help_text=_("The participant is not allowed to deselect this product"), default=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(_("name"), max_length=100)
    price = models.DecimalField(_("price"), max_digits=8, decimal_places=2)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return self.name


class Document(models.Model):
    event = models.ForeignKey("Event", related_name="documents", on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=100)
    document = models.FileField(_("document"), upload_to="dokumente")
    u18 = models.BooleanField(_("u18"), default=False, help_text="Only required for persons under 18 years.")
    upload = models.BooleanField(_("require upload"), default=False, help_text="Document needs to be signed and uploaded back to the system.")
    order = models.PositiveIntegerField(_("order"), default=0)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("document")
        verbose_name_plural = _("documents")
        ordering = ("order", "name")


def anhang_path(instance, filename):
    return "attachments/%s/%s" % (instance.booking.code, filename)


class Attachment(models.Model):
    booking = models.ForeignKey("Booking", on_delete=models.CASCADE)
    document = models.ForeignKey("Document", on_delete=models.CASCADE)
    file = models.FileField(upload_to=anhang_path)
    date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("booking", "document")
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")


class Day(models.Model):
    event = models.ForeignKey("event", on_delete=models.CASCADE, related_name="days")
    day = models.CharField("Tag", max_length=100)

    arrival = models.BooleanField(_("arrival day"), default=False)
    departure = models.BooleanField(_("departure day"), default=False)
    
    order = models.PositiveIntegerField(_("order"), default=0)

    def __str__(self):
        return self.tag

    class Meta:
        verbose_name = _("day")
        verbose_name_plural = _("days")
        ordering = ("order", "day")


class Discipline(models.Model):
    event = models.ForeignKey("event", on_delete=models.CASCADE, related_name="disciplines")
    code = models.CharField(max_length=10)
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField("Sortierung", default=0)

    def __str__(self):
        return self.label
    
    class Meta:
        verbose_name = _("discipline")
        verbose_name_plural = _("disciplines")
        ordering = ("order", "code")


class WebPage(models.Model):
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="seiten")
    slug = models.SlugField(default="home")
    name = models.CharField(max_length=30)
    icon = models.CharField(max_length=30, default="home", help_text=_("Name of a fontawesome icon to display in the menu"))
    html = RichTextUploadingField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    menu = models.BooleanField(_("Visible in the menu"), default=True)

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")
        unique_together = ("event", "slug")
        ordering = ("order",)


def generate_code():
    return "".join(random.choice(string.ascii_lowercase+string.digits) for i in range(8))


class Booking(models.Model):
    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    code = models.CharField(_("code"), max_length=8, unique=True, default=generate_code)
    date = models.DateTimeField(_("date"), auto_now_add=True)
    checkin_date = models.DateTimeField(_("check-in date"), null=True, blank=True, editable=False)

    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100)
    sex = models.CharField(_("sex"), max_length=1, choices=GESCHLECHT_CHOICES, null=True, blank=True)

    email = models.EmailField(_("e-mail"))
    club = models.CharField(_("club"), max_length=100, blank=True)
    date_of_birth = models.DateField(_("date of birth"))

    address = models.CharField(_("address"), max_length=255, blank=True, null=True)
    zipcode = models.CharField(_("zip code"), max_length=20, blank=True, null=True)
    city = models.CharField(_("city"), max_length=100, blank=True, null=True)
    country = CountryField(_("country"), default="DE", blank=True, null=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True, null=True)

    food = models.CharField(_("food"), max_length=15, choices=ESSEN_CHOICES)
    arrival = models.ForeignKey("Day", null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("arrival"), related_name="booking_arrival")
    departure = models.ForeignKey("Day", null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("departure"), related_name="booking_departure")
    rate = models.ForeignKey("Rate", null=True, blank=True, on_delete=models.SET_NULL)
    disciplines = models.ManyToManyField("Discipline", blank=True)

    notes = models.TextField(_("notes"), blank=True)

    amount = models.DecimalField(_("amount"), editable=False, max_digits=8, decimal_places=2, default=0, help_text="Gesamter vom Teilnehmer zu zahlender Betrag. Wird automatisch berechnet.")
    state = models.CharField(_("state"), max_length=15, choices=STATUS_CHOICES, default="open")

    internal_notes = models.TextField(_("internal notes"), blank=True)

    def get_absolute_url(self):
        return reverse("convention:show-booking", args=[self.event.slug]) + "?" + urlencode({ "code": self.code, "email": self.email })

    def calc_betrag(self):
        betrag = 0

        # TODO: Calculate amount

        return betrag


    def age(self):
        age = relativedelta(self.event.begin_date.date(), self.date_of_birth)
        return age

    def full_age(self):
        age = self.age()
        if age.years >= 18:
            return True
        else:
            return False

    class Meta:
        verbose_name = _("booking")
        verbose_name_plural = _("bookings")

        ordering = ("-date",)

    def __str__(self):
        return self.code


TRANS_TYP_CHOICES = (
    ("incoming", _("incoming payment")),
    ("credit", _("credit")),
    ("refund", _("refund")),
    ("other", _("other")),
)

TRANS_MITTEL_CHOICES = (
    ("paypal", _("PayPal")),
    ("cash", _("cash")),
    ("wire", _("wire transfer")),
    ("internal", _("internal transfer")),
)


class Transaction(models.Model):
    booking = models.ForeignKey("Booking", on_delete=models.CASCADE, verbose_name="Buchung")
    typ = models.CharField("Typ", max_length=15, choices=TRANS_TYP_CHOICES)
    mittel = models.CharField("Zahlungsmittel", max_length=15, choices=TRANS_MITTEL_CHOICES)
    nr = models.CharField("Nr.", max_length=255, blank=True, default="", help_text="Nr. der Transaktion beim Zahlungsdienstleister, falls vorhanden")
    betrag = models.DecimalField("Betrag", max_digits=8, decimal_places=2, default=0, help_text="Bei ausgehenden Zahlungen bitte negatives Vorzeichen benutzen")
    gebuehr = models.DecimalField("Gebühr", max_digits=8, decimal_places=2, default=0, help_text="Transaktionsgebühr (z.B. bei PayPal)")
    grund = models.CharField(max_length=255, blank=True, default="")
    datum = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

        ordering = ("-datum",)

    def __str__(self):
        return str(self.id)
