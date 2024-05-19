from django.contrib import admin
from .models import Poll, Question, Choice, TgUser, Answer, Thread, Message


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]
    


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question_type', 'poll')
    list_filter = ('question_type', 'poll')
    search_fields = ('text',)
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question')
    list_filter = ('question',)
    search_fields = ('text',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('tg_user', 'question', 'choice', 'response')
    list_filter = ('question', 'tg_user')
    search_fields = ('response',)


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('tg_user', 'poll', 'created_at')
    list_filter = ('poll', 'created_at')
    search_fields = ('tg_user__tg_username', 'poll__title')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'text', 'sent_by_bot', 'timestamp')
    list_filter = ('sent_by_bot', 'timestamp')
    search_fields = ('text',)
