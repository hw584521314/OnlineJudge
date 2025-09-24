from utils.api import UsernameSerializer, serializers
from .models import Exam,ExamDetail,ExamToExamDetail,StudentProfile,ExamResult
from account.serializers import UserSerializer
from problem.serializers import ProblemSerializer
from problem.models import Problem

class BaseExamSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    desc=serializers.CharField(required=False, allow_blank=True,default="")
    enable=serializers.BooleanField()
    
    class Meta:
        model = Exam
        fields=(
            "title",
            "start_time",
            "end_time",
            "desc",
            "enable",
        )



class CreateExamSerializer(BaseExamSerializer):
    pass

class ExamDetailProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = (
            "id",
            "_id",
            "title",            
            
        )


class ExamDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    problems = serializers.SerializerMethodField()

    class Meta:
        model = ExamDetail
        fields = [ 'id','name','desc',   'create_time','enable', 'problems']
    
    def get_problems(self, obj):
        return [
            {
                "problem": ExamDetailProblemSerializer(p["problem"]).data,
                "score": p["score"]
            }
            for p in obj.get_problems_config()
        ]
    
class ExamSerializer(BaseExamSerializer):
    id = serializers.IntegerField()
    create_user=UserSerializer(required=False)
    exam_details=serializers.SerializerMethodField()
    
    def get_exam_details(self, obj):
        #遍历其exam_details属性
        return [
            {
                "exam_detail": ExamDetailSerializer(each["exam_detail"]).data,
                "category": each["category"]
            }
            for each in obj.exam_details
        ]
    class Meta(BaseExamSerializer.Meta):
        fields = BaseExamSerializer.Meta.fields + (
            "id",
            "create_user",
            "exam_details"
        )


class StudentSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    class Meta:
        model = StudentProfile
        fields = [
            "id","name","sid", "s_class", "sub_college", "profession", "create_time", 'enable'
        ]

class ExamResultSerializer(serializers.ModelSerializer):
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    #answers=serializers.SerializerMethodField()
    class Meta:
        model = ExamResult
        fields=["answers", "total_score", "update_time"]
    
    # def get_answers(self, obj):
    #     [ for i in obj.answers]
    #     return obj.answers

class StudentExamResultListSerializer(serializers.ModelSerializer):
    # 如果需要展示 exam 的详细信息，可以使用嵌套序列化器
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    start_time = serializers.DateTimeField(source='exam.start_time', format="%Y-%m-%d %H:%M:%S", read_only=True)
    end_time = serializers.DateTimeField(source='exam.end_time', format="%Y-%m-%d %H:%M:%S", read_only=True)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    class Meta:
        model = ExamResult
        fields=["id","exam_title","total_score","start_time","end_time","update_time"]