from django.conf.urls import url
from ..views.oj import Typing, TypingHistoryView

urlpatterns = [
    url(r"^typing/?$", Typing.as_view(), name="typing_api"), 
    url(r"^typing_history/?$", TypingHistoryView.as_view(), name="typing_history_api"),   
]