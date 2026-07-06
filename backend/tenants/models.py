import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    """
    Represents the global organization (Condominium or Residential Complex in Venezuela).
    Acts as the root of data isolation for multi-tenancy.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        help_text="Name of the condominium (e.g., Residencias Los Sauces)",
    )
    subdomain = models.CharField(
        max_length=50,
        unique=True,
        help_text="Subdomain for routing purposes (e.g., lossauces)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Circuit breaker switch to suspend services due to non-payment",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.subdomain})"


class User(AbstractUser):
    """
    Custom User Model that extends Django's native authentication
    to support Aporte's three-tier access hierarchy.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Global Platform Admin (Aporte Team)"
        CONDO_ADMIN = "CONDO_ADMIN", "Condominium Administrator (Board/Management Co.)"
        RESIDENT = "RESIDENT", "Resident / Coproprietary"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RESIDENT,
        help_text="Hierarchical security role within the platform",
    )

    # Multi-tenant Relationship: Super-Admins have no tenant context, local managers and residents do.
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text="Condominium cluster the user belongs to",
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Primary phone contact information",
    )

    def __str__(self):
        return f"{self.username} - {self.role} ({self.tenant.subdomain if self.tenant else 'GLOBAL'})"


class Property(models.Model):
    """
    Represents an individual physical unit (apartment, townhouse, or commercial spot)
    within a specific condominium cluster.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Strict multi-tenant scoping boundary
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="properties",
        help_text="The condominium complex this unit belongs to",
    )

    unit_number = models.CharField(
        max_length=20,
        help_text="The apartment or house number (e.g., Apt 4B, House 12)",
    )
    floor = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="The building floor where the unit is located (if applicable)",
    )
    block_or_tower = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tower or section indicator (e.g., Tower A, Phase II)",
    )

    # Financial allocation metadata
    aliquot = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="The property's participation percentage in general expenses (e.g., 0.0250 for 2.5%)",
    )

    # Optional direct correlation back to an owner profile
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_properties",
        help_text="The primary user registered as the legal owner of this unit",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Properties"
        # Enforce unique unit names within the exact same condominium
        unique_together = ("tenant", "unit_number", "block_or_tower")

    def __str__(self):
        prefix = f"{self.block_or_tower} - " if self.block_or_tower else ""
        return f"{self.tenant.subdomain.upper()} | {prefix}Unit {self.unit_number}"


class BoardBankAccount(models.Model):
    """
    Represents an official financial account owned and managed by a condominium board.
    Configured to hold standard wire transfer parameters and specific Venezuelan Pago Móvil metadata.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Strict multi-tenant scoping boundary
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="bank_accounts",
        help_text="The condominium complex that owns this financial account",
    )

    bank_name = models.CharField(
        max_length=100,
        help_text="Official bank entity name (e.g., Banesco, Banco de Venezuela)",
    )
    account_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="The full 20-digit standard Venezuelan bank account number",
    )

    # Venezuelan localized Pago Móvil parameters
    pago_movil_phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="The telephone number linked to the Pago Móvil channel",
    )
    pago_movil_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="The fiscal ID (Cédula or RIF) bound to the Pago Móvil registry",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Status flag to enable or disable this account for resident visibility",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        channel_type = "Pago Móvil" if self.pago_movil_phone else "Wire Transfer Only"
        return f"{self.tenant.subdomain.upper()} | {self.bank_name} ({channel_type})"
