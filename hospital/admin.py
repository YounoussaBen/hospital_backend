from django.contrib import admin
from .models import DoctorNote, ActionableStep

class ActionableStepInline(admin.TabularInline):
    model = ActionableStep
    extra = 0
    readonly_fields = ('id',)
    fields = ('id', 'step_type', 'description', 'schedule', 'status')
    show_change_link = True

@admin.register(DoctorNote)
class DoctorNoteAdmin(admin.ModelAdmin):
    # Assuming your BaseModel adds a 'created' field
    list_display = ('id', 'doctor', 'patient', 'get_note_excerpt')
    list_filter = ('doctor', 'patient')
    search_fields = ('doctor__email', 'patient__email', 'note_text')
    inlines = [ActionableStepInline]

    def get_note_excerpt(self, obj):
        # Display first 50 characters of the note_text field
        text = obj.note_text or ""
        return f"{text[:50]}..." if len(text) > 50 else text
    get_note_excerpt.short_description = "Note Excerpt"


@admin.register(ActionableStep)
class ActionableStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'step_type', 'get_description_excerpt', 'status', 'schedule')
    list_filter = ('step_type', 'status')
    search_fields = (
        'description', 
        'note__doctor__email', 
        'note__patient__email'
    )
    actions = ['mark_as_completed', 'mark_as_cancelled']

    def get_description_excerpt(self, obj):
        text = obj.description or ""
        return f"{text[:50]}..." if len(text) > 50 else text
    get_description_excerpt.short_description = "Description"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} actionable step(s) marked as completed.")
    mark_as_completed.short_description = "Mark selected steps as completed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} actionable step(s) marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected steps as cancelled"
