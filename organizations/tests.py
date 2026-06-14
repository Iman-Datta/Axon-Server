from django.test import TestCase



class OrganizationMember(models.Model):

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"
        


    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members"
    )


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships"
    )


    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )


    joined_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "user"
                ],
                name="unique_organization_member"
            )
        ]


    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.organization.name}"
        )