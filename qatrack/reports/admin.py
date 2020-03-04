from django.conf import settings
from django.contrib import admin
import django.forms as forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from qatrack.qatrack_core.admin import BaseQATrackAdmin, BasicSaveUserAdmin
from qatrack.reports.models import ReportSchedule, SavedReport


class SavedReportAdmin(BaseQATrackAdmin):

    list_display = (
        "title",
        "report_type",
        "report_format",
        "created_by",
        "created",
    )

    list_filter = [
        "report_type",
        "report_format",
    ]

    search_fields = [
        "title",
        "created_by__username",
        "modified_by__username",
    ]

    def has_add_permission(self, request):
        return False


class ReportScheduleForm(forms.ModelForm):

    class Meta:

        model = ReportSchedule
        fields = (
            "report",
            "schedule",
            "time",
            "groups",
            "users",
            "emails",
        )

    def clean(self):

        cleaned_data = super().clean()
        no_groups = len(cleaned_data.get('groups', [])) == 0
        no_users = len(cleaned_data.get('users', [])) == 0
        no_emails = len([x for x in cleaned_data.get("emails", "").split(",") if x]) == 0
        if no_groups and no_users and no_emails:
            msg = _("You must select at least one group, user, or email address!")
            self.add_error(None, forms.ValidationError(msg))

        return cleaned_data


class ReportScheduleAdmin(BasicSaveUserAdmin):

    form = ReportScheduleForm

    list_display = (
        'get_report_title',
        'get_report_type',
        'get_report_format',
        'schedule',
        'last_sent',
        'created_by',
        'created',
    )

    list_filter = (
        "report__report_type",
    )

    search_fields = [
        "title",
        "report__report_type",
        "created_by__username",
        "modified_by__username",
    ]

    class Media:
        js = (
            settings.STATIC_URL + "jquery/js/jquery.min.js",
            settings.STATIC_URL + "select2/js/select2.js",
            settings.STATIC_URL + "js/reportschedule_admin.js",
        )
        css = {
            'all': (
                settings.STATIC_URL + "select2/css/select2.css",
            ),
        }

    def get_queryset(self, request):  # pragma: nocover
        qs = super().get_queryset(request).prefetch_related("groups", "users")
        return qs

    def get_report_type(self, obj):
        return obj.report.get_report_type_display()
    get_report_type.admin_order_field = "report__report_type"
    get_report_type.short_description = _l("Report Type")

    def get_report_format(self, obj):
        return obj.report.get_report_format_display()
    get_report_format.admin_order_field = "report__report_format"
    get_report_format.short_description = _l("Report Format")

    def get_report_title(self, obj):
        return obj.report.title
    get_report_title.admin_order_field = "report__report_title"
    get_report_title.short_description = _l("Report Title")


admin.site.register([SavedReport], SavedReportAdmin)
admin.site.register([ReportSchedule], ReportScheduleAdmin)
