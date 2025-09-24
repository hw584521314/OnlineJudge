from django.conf.urls import url
from ..views.oj import *

#用户级别
urlpatterns = [

    url(r"^exam/get_list/?$", StudentExamList.as_view(), name="student_exam_get_list_api"),
    url(r"^exam/get/?$", StudentExam.as_view(), name="student_exam_get_api"),
    url(r"^exam/exam_detail/get/?$", StudentExamDetail.as_view(), name="student_examDetail_get_api"),
    url(r"^exam/problem/?$", ExamProblemAPI.as_view(), name="exam_problem_api"),
    url(r"^exam/submissions/?$", ExamSubmissionListAPI.as_view(), name="exam_submissions_api"),
    url(r"^exam/result/get/?$", ExamResultAPI.as_view(), name="exam_result_api"),
    url(r"^exam/get_result_list/?$", StudentExamResultListAPI.as_view(), name="exam_result_list_api"),
]