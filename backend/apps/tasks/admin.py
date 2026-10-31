from django.contrib import admin

from .models import BaleLink, BaleMessage, Task, TaskEvent


class TaskEventInline(admin.TabularInline):
    model = TaskEvent
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["number", "kind", "status", "customer", "assignee", "created_by", "created_at"]
    list_filter = ["kind", "status"]
    search_fields = ["number", "text", "customer_name"]
    inlines = [TaskEventInline]


admin.site.register(BaleLink)


@admin.register(BaleMessage)
class BaleMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "chat_id", "status", "attempts", "created_at"]
    list_filter = ["status"]
