from exam.serializers import ExamDetailSerializer,ExamResultSerializer,StudentExamResultListSerializer
from problem.models import Problem
from problem.serializers import ProblemSerializer
from submission.models import Submission
from submission.serializers import SubmissionListSerializer
from utils.api  import serializers
from account.decorators import login_required
from utils.api import APIView
from ..models import Exam, ExamDetail, ExamToExamDetail, StudentProfile, ExamResult, StudentToExam
from django.utils import timezone
from datetime import timedelta
from account.decorators import check_exam_permission
from django.db.models import Max, Value
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class StudentExamListSerializer(serializers.ModelSerializer):
    start_time=serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    end_time=serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    #计算字段 #0 未开始 1 进行中 2 结束
    #status = serializers.SerializerMethodField()
    class Meta:
        model = Exam
        fields = ['id', 'title', 'desc','status', 'start_time', 'end_time']
    


class StudentExamList(APIView):
    @login_required
    def get(self, request):
        user = request.user
        #查询这之后一个月内的考试
        exams=Exam.objects.filter(start_time__range=(timezone.localtime(timezone.now())+timedelta(days=-15),timezone.localtime(timezone.now())+timedelta(days=30)),enable=True)
        return self.success({"data":StudentExamListSerializer(exams, many=True).data,"total":len(exams)})


class StudentExam(APIView):
    @login_required
    def get(self, request):
        exam_id = request.GET.get('id')
        user = request.user
        # if not user.student_profile.can_take_exam(Exam.objects.get(id=exam_id)):
        #     return self.error("No permission")
        exam = Exam.objects.get(id=exam_id)
        if exam.status==0:
            return self.error("Exam has not started")
        elif exam.status==2:
            return self.error("Exam has ended")
        server_time = timezone.now()
        #格式转为：format="%Y-%m-%d %H:%M:%S"
        server_time = server_time.strftime("%Y-%m-%d %H:%M:%S")
        return self.success({"data":StudentExamListSerializer(exam).data, "server_time":server_time})
    
class StudentExamDetail(APIView):
    @login_required
    def get(self, request):
        exam_id = request.GET.get('id')
        user = request.user
        student=StudentProfile.objects.get(user=user.id);#  user.studentprofile
        # 根据学号的奇偶性决定从exam_details的catagory中取哪套试卷
        if student.sid[-1] in ['1','3','5','7','9']:
            
            exam_detail=ExamDetail.objects.filter(examtoexamdetail__exam=exam_id, examtoexamdetail__category='A').first()
        else:
            exam_detail=ExamDetail.objects.filter(examtoexamdetail__exam=exam_id, examtoexamdetail__category='B').first()
        return self.success(ExamDetailSerializer(exam_detail).data)


class ExamProblemAPI(APIView):

    #@check_exam_permission(check_type="problems")
    @login_required
    def get(self, request):
        problem_id = request.GET.get("problem_id")
        if problem_id:
            try:
                problem = Problem.objects.select_related("created_by").get(id=problem_id)
            except Problem.DoesNotExist:
                return self.error("Problem does not exist.")
            #if self.exam.problem_details_permission(request.user):
            problem_data = ProblemSerializer(problem).data  
            
            return self.success(problem_data)
        
class StudentExamResultListAPI(APIView):
    '''
    获取学生的所有历史考试数据
    '''
    @login_required
    def get(self, request):
        page_index = request.GET.get("page",1)
        page_size = request.GET.get("limit",10)
        
        exam_results = ExamResult.objects.filter(student__user_id=request.user.id).select_related("exam").order_by("-create_time")
        paginator = Paginator(exam_results, page_size)  # 每页显示 10 条记录
        try:
            exam_results = paginator.page(page_index)
        except PageNotAnInteger:
            # 如果页码不是一个整数，则返回第一页的结果
            exam_results = paginator.page(1)
        except EmptyPage:
            # 如果页码超出了最大页数，则返回最后一页的结果
            exam_results = paginator.page(paginator.num_pages)
        
        data=StudentExamResultListSerializer(exam_results, many=True).data
        return self.success({"data":data,"total":paginator.count})
        



class ExamSubmissionListAPI(APIView):
    #@check_contest_permission(check_type="submissions")
    @login_required
    def get(self, request):
        if not request.GET.get("limit"):
            return self.error("Limit is needed")

        exam_id = request.GET.get("exam_id")
        if not exam_id:
            return self.error("Exam id is needed")
        #如果是管理员，则所有提交都可以查看
        if not request.user.is_admin_role():
            submissions = Submission.objects.filter(exam__id=exam_id,user_id=request.user.id).select_related("problem__created_by")
        else:
            submissions = Submission.objects.filter(exam__id=exam_id).select_related("problem__created_by")
        problem_id = request.GET.get("problem_id")
        
        result = request.GET.get("result")
        
        if problem_id:
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                return self.error("Problem doesn't exist")
            submissions = submissions.filter(problem=problem)

        if result:
            submissions = submissions.filter(result=result)



        data = self.paginate_data(request, submissions)
        data["results"] = SubmissionListSerializer(data["results"], many=True, user=request.user).data
        return self.success(data)
    



class ExamResultAPI(APIView):
    @login_required
    def get(self, request):
        user_id = request.user.id
        exam_id= request.GET.get("exam_id")
        exam_detail_id=request.GET.get("exam_detail_id")
        if not exam_id:
            return self.error("Exam id is needed")
        if not exam_detail_id:
            return self.error("Exam detail id is needed")
        #获取用于在该次考试中提交过的相同题目的最高分，其中分数在static_info这个JSON字段的score字段中
        # 获取用于在该次考试中提交过的相同题目的最高分，其中分数在static_info这个JSON字段的score字段中
        student=StudentProfile.objects.get(user_id=user_id)
        exam_result=ExamResult.objects.filter(exam_id=exam_id,student=student).first()
        data=ExamResultSerializer(exam_result).data
        return self.success(data=data)


