from django.db import models
from django.db.models import JSONField,F

from account.models import User,AdminType
from contest.models import Contest
from utils.models import RichTextField
from utils.constants import Choices


#组卷的试卷
class ExamDetail(models.Model):
    class Meta:
        db_table = "exam_detail"
    name=models.TextField()
    desc=RichTextField(default="")
    create_time = models.DateTimeField(auto_now_add=True)
    enable=models.BooleanField(default=True)
    
    # 题目分类 A,B
    problems = JSONField()
    # [{id: 1, score: 10}, {id: 2, score: 20}]
    def get_problems_config(self):
        from problem.models import Problem
        problems = []
        for problem in self.problems:
            try:
                problems.append({"problem":Problem.objects.get(id=problem["id"]),"score":problem["score"]})
            except Problem.DoesNotExist:
                pass
        return problems
    @property
    def exams(self):
        # 获取所有的考试
        result=[]
        for relation in ExamToExamDetail.objects.filter(exam_detail=self):
            result.append((relation.exam,relation.category))
        return result



class Exam(models.Model):
    class Meta:
        db_table = "exam"
        #unique_together = (("_id", "contest"),)
        #ordering = ("create_time",)
    title=models.CharField(max_length=255,default="")
    start_time=models.DateTimeField()
    end_time=models.DateTimeField()
    #status=models.IntegerField(default=0) #0 未开始 1 进行中 2 结束
    desc=RichTextField(default="")
    enable=models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    create_user = models.ForeignKey(User, on_delete=models.CASCADE)
    #添加一个计算属性status，表示考试的状态
    @property
    def status(self):
        from django.utils import timezone
        now = timezone.localtime(timezone.now())
        
        if now < self.start_time:
            return 0 #未开始
        elif now > self.end_time:
            return 2 #结束
        else:
            return 1 #进行中
    @property
    def exam_details(self):
        # 获取所有的试卷
        result=[]
        for relation in ExamToExamDetail.objects.filter(exam=self):
            result.append({"exam_detail":relation.exam_detail,"category":relation.category})
        return result


class ExamToExamDetail(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    exam_detail = models.ForeignKey(ExamDetail, on_delete=models.CASCADE)
    category = models.CharField(max_length=10)  # 如 A/B 卷分类

    class Meta:
        db_table = "exam_to_exam_detail"
        unique_together = (('exam', 'exam_detail'),)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    name=models.TextField()#姓名
    sid=models.TextField()#学号
    sub_college=models.TextField() #学院
    s_class=models.TextField() #班级
    profession=models.TextField() #专业

    create_time = models.DateTimeField(auto_now_add=True)
    enable=models.BooleanField(default=True)
    exam_permissions = models.TextField(default="read")  # 示例字段
    
    # 可以添加针对考试场景的方法
    def can_take_exam(self, exam):
        return self.user.is_authenticated and (self.user.admin_type in [AdminType.ADMIN, AdminType.SUPER_ADMIN,AdminType.STUDENT] )

    class Meta:
        db_table = "student_profile"



class ExamResult(models.Model):
    class Meta:
        db_table = "exam_result"


    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    answers  = JSONField()
    #小数类型
    total_score = models.DecimalField (max_digits=10, decimal_places=2,default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
#考试和学生的绑定关系
class StudentToExam(models.Model):
    class Meta:
        db_table = "student_to_exam"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    
