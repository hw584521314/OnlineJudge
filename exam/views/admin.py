from datetime import datetime, timezone

import urllib
from account import serializers
from utils.api import APIView,validate_serializer
from ..models import Exam, ExamDetail, StudentProfile, ExamResult,ExamToExamDetail
#导入account应用中的User模型
from account.models import User,AdminType, UserProfile
from account.decorators import admin_role_required, login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..serializers import ExamSerializer,CreateExamSerializer,ExamDetailSerializer, StudentSerializer,ExamResultSerializer,StudentExamResultListSerializer
from rest_framework.response import Response
from django.db import IntegrityError 
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import FileResponse
from rest_framework.parsers import MultiPartParser,FormParser
import pandas as pd
from io import BytesIO
from django.utils.encoding import escape_uri_path
import os
from django.db.models import Q
import json
'''
admin/exam/create

'''
class ExamCreate(APIView):
    """
    创建考试
    """
    @admin_role_required
    @validate_serializer(CreateExamSerializer)
    def post(self, request):
        data = request.data
        exam = Exam.objects.create(
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            enable=data.get('enable'),  
            desc=data.get('desc',""), 
            title=data.get('title'),         
            create_user=request.user
        )
        return self.success(data={'id':exam.id})

'''
admin/exam/get
'''
class ExamGet(APIView):
    @login_required
    def get(self, request):
        """
        获取某场考试信息
        """
        exam_id = request.GET.get('id')
        if not exam_id:
            return self.error("exam_id is required")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return self.error("exam not found")
        
        return self.success(data=ExamSerializer(exam).data)
        


'''
admin/exam/get_list
'''
class ExamList(APIView):
    """
    获取所有考试信息
    """
    @admin_role_required
    def get(self, request):
        """
        获取所有考试信息
        """
        numbers_per_page = request.GET.get('nums_per_page', 10)
        page_index = request.GET.get('page_idx', 1)
        keyword = request.GET.get('keyword', '')
        #这里能实现nested查询，获取考试创建者的信息
        if keyword:
            exams = Exam.objects.filter(
                Q(id__icontains=keyword)|Q(title__icontains=keyword) #| Q(desc__icontains=keyword)
            ).order_by("-id").select_related('create_user').all()
        else:
            exams = Exam.objects.order_by("-id").select_related('create_user').all()
        paginator = Paginator(exams, numbers_per_page)  # 每页显示 10 条记录
        try:
            exam_list = paginator.page(page_index)
        except PageNotAnInteger:
            # 如果页码不是一个整数，则返回第一页的结果
            exam_list = paginator.page(1)
        except EmptyPage:
            # 如果页码超出了最大页数，则返回最后一页的结果
            exam_list = paginator.page(paginator.num_pages)
        exam_list = list(exam_list)
        
        data=ExamSerializer(exam_list, many=True).data
        
        return self.success({"data":data,"total":paginator.count})
        
        
'''
admin/exam/update
'''
class ExamUpdate(APIView):
    """
    更新考试信息
    """
    @admin_role_required    
    def post(self, request):
        data = request.data
        exam_id = data.get('id')
        if not exam_id:
            return self.error("exam_id is required")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return self.error("exam not found")
        exam.start_time = data.get('start_time', exam.start_time)
        exam.end_time = data.get('end_time', exam.end_time)
        exam.enable = data.get('enable', exam.enable)
        exam.enable = data.get('enable', exam.enable)
        exam.desc = data.get('desc', exam.desc)
        exam.title = data.get('title', exam.title)
        exam.save()
        return self.success(data=exam.id)

'''
admin/exam/delete
'''
class ExamDelete(APIView):
    """
    删除考试
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        exam_id = data.get('id')
        if not exam_id:
            return self.error("exam_id is required")
        try:
            exam = Exam.objects.get(id=exam_id)
            exam.delete()
            return self.success(data=exam.id)
        except Exam.DoesNotExist:
            return self.error("exam not found")

'''
admin/exam/export_result
'''
class ExamExportResult(APIView):
    """
    导出考试结果
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        exam_id = data.get('exam_id')
        if not exam_id:
            return self.error("exam_id is required")
        
        #将ExamResult的结果同Exam，ExamDetail,StudentProfile关联查询以便获取更多的列
        exam_results=ExamResult.objects.filter(exam_id=exam_id)
        if not exam_results:
            return self.error("no exam results")
        '''
        生成excel文件
        处理answers字段，解析json，其格式为：
        [{"name": "a-b问题", "max_score": 100, "sub_score": 50.0, "problem_id": 3, "problem_score": 100, "exam_config_score": 50.0}, {"name": "a+b problem", "max_score": 99, "sub_score": 50.0, "problem_id": 1, "problem_score": 99, "exam_config_score": 50.0}]
        解析后将里面变为多列
        '''

        df=pd.DataFrame(list(exam_results.values()))
        #将answers变为多行
        # 1. 解析 answers 列：字符串 → 列表 of dict
        #df['answers'] = df['answers'].apply(json.loads)
        # 2. 展开 answers 列（每条 answer 变成一行）
        df_exploded = df.explode('answers').reset_index(drop=True)
        # 3. 将 answers 字典展开为多个列
        answers_df = pd.json_normalize(df_exploded['answers'])
        # 4. 保留其他列（非 answers 列）
        meta_cols = ['id', 'total_score', 'create_time', 'update_time', 'exam_id', 'student_id']
        meta_df = df_exploded[meta_cols]
        
        # 8. 拼接最终 DataFrame
        df = pd.concat([meta_df, answers_df], axis=1)
        #print(df.head(2))
        #添加学生信息   
        df_student=pd.DataFrame(list(StudentProfile.objects.filter(id__in=df['student_id'].tolist()).values('id','sid','name','s_class','profession','sub_college')))
        df=pd.merge(df,df_student,left_on='student_id',right_on='id',how='left')
        #添加考试信息       
        df_exam=pd.DataFrame(list(Exam.objects.filter(id=exam_id).values('id','title','start_time','end_time','desc')))
        df=pd.merge(df,df_exam,left_on='exam_id',right_on='id',how='left',suffixes=('', '_exam'))
        
        #重新排序列
        cols=['id_x','create_time','update_time','exam_id',
              "student_id","sid","name_y","s_class","profession","sub_college","title","start_time",
              "end_time","name_x","max_score","sub_score","problem_id","problem_score","exam_config_score","total_score"
]
        df=df[cols]
        #重命名列
        df.columns=[
            "结果编码ID", "结果创建时间","结果更新时间",
            "考试ID","学生ID","学号","姓名","班级","专业","学院",
            "考试标题","考试开始时间","考试结束时间",
            "题目","提交最高分","提交换算分","题目ID","题目原始分","题目配置分",
            "总分"]
        # 在保存Excel文件之前添加以下代码
        # 移除所有带时区的datetime列的时区信息
        for col in df.columns:
            if pd.api.types.is_datetime64tz_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)
        #保存excel文件到服务器，命名添加时间信息
        filename="考试结果_"+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+".xlsx"
        save_path=os.path.join(settings.UPLOAD_DIR, filename)   
        df.to_excel(save_path, index=False)
        #这里的url_path是/api/exam/export_result?filename=xxx。
        url_path=f"/admin/exam/export_result?filename={filename}"
        return self.success(data={'url': f"{url_path}", 'message': '点击链接下载文件'})
    
    
    
    @admin_role_required
    def get(self, request):
        '''
        返回客户端想下载的文件
        '''
        filename = request.GET.get('filename')
        if not filename:
            return self.error("filename is required")
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return self.error("file not found")
        
        # 使用 FileResponse 直接返回文件
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        response['Content-Disposition'] = f'attachment; filename=export_result.xlsx'
        return response


'''
admin/exam/exam_detail/create

'''
class ExamDetailCreate(APIView):
    """
    创建考试题目
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        exam_name = data.get('name')
        if not exam_name:
            return self.error("exam_name is required")
        #查一下数据库中是否存在，如果已经存在，返回存在同名的试卷，否则继续往下新建试卷
        if ExamDetail.objects.filter(name=exam_name).exists():
            return self.error("exam_name is already exists")
        desc=data.get('desc',"")
        enable=data.get('enable',True)
        examDetail = ExamDetail.objects.create(name=exam_name,desc=desc,enable=enable,problems=[])
  
        return self.success(data=examDetail.id)

'''
admin/exam/exam_detail/get
'''
class ExamDetailGet(APIView):
    @admin_role_required
    def get(self, request):
        """
        获取试卷信息
        """
        exam_deital_id = request.GET.get('id')
        
        if not exam_deital_id:
            return self.error("exam_deital_id is required")
        try:
            exam_detail = ExamDetail.objects.get(id=exam_deital_id)
        except ExamDetail.DoesNotExist:
            return self.error("exam detail not found")
          
        
        data = ExamDetailSerializer(exam_detail).data
        return self.success(data=data)

class ExamDetailOfExam(APIView):
    """
    获取考试的试卷列表
    """
    @admin_role_required
    def get(self, request):
        """
        获取考试的试卷列表
        """
        exam_id = request.GET.get('id')
        category = request.GET.get('category')
        if not exam_id:
            return self.error("exam_id is required")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return self.error("exam not found")
        
        exam_detail = None
        for each in exam.exam_details:
            if each.get("category") == category:
                exam_detail = each.get("exam_detail")
                break
        if exam_detail is None:
            return self.error("还未配置试卷")
        #print(exam_detail)
        data = ExamDetailSerializer(exam_detail).data
        return self.success(data=data)
    
    @admin_role_required
    def post(self, request):
        data = request.data
        exam_id = data.get('exam_id')
        category = data.get('category')
        exam_detail_id = data.get('exam_detail_id')
        if not exam_id:
            return self.error("exam_id is required")
        if not category:
            return self.error("category is required")
        
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return self.error("exam not found")


        
        #查询原来的关系，若存在，则更新，否则，则新建
        exam_to_detail=ExamToExamDetail.objects.filter(exam=exam,category=category).first()
        if exam_to_detail:
            if not exam_detail_id:
                #如果没有传入试卷id，则删除
                exam_to_detail.delete()
                return self.success(data=exam_to_detail.id)
            
            try:
                exam_detail = ExamDetail.objects.get(id=exam_detail_id)
            except ExamDetail.DoesNotExist:
                return self.error("exam detail not found")
            #更新
            exam_to_detail.exam_detail=exam_detail
            exam_to_detail.category=category
            exam_to_detail.save()
        else:
            #新建
            try:
                try:
                    exam_detail = ExamDetail.objects.get(id=exam_detail_id)
                except ExamDetail.DoesNotExist:
                    return self.error("exam detail not found")
                exam_to_exam_detail = ExamToExamDetail.objects.create(
                    exam=exam,
                    exam_detail=exam_detail,
                    category=category
                )
                exam_to_exam_detail.save()
            except IntegrityError:
                return self.error("A/B卷试题一样！")
        return self.success(data=exam_detail.id)

'''
admin/exam/exam_detail/get_list
'''
class ExamDetailList(APIView):
    """
    获取所有试卷列表
    """
    @admin_role_required
    def get(self, request):
        """
        获取所有试卷列表
        """
        numbers_per_page = request.GET.get('nums_per_page', 10)
        page_index = request.GET.get('page_idx', 1)
        enable=request.GET.get('enable')
        keyword=request.GET.get('keyword') #从name或者desc字段搜索keyword的like 搜索
        exam_details = ExamDetail.objects.order_by('-id')

        if enable=="true":
            exam_details = exam_details.filter(enable=True)

        if keyword:
            exam_details = exam_details.filter(
                Q(id__icontains=keyword)|Q(name__icontains=keyword) | Q(desc__icontains=keyword)
            )
            
        
        #exam_details = exam_details.all()
        
        paginator = Paginator(exam_details, numbers_per_page)  # 每页显示 10 条记录
        try:
            exam_detail_list = paginator.page(page_index)
        except PageNotAnInteger:
            # 如果页码不是一个整数，则返回第一页的结果
            exam_detail_list = paginator.page(1)
        except EmptyPage:
            # 如果页码超出了最大页数，则返回最后一页的结果
            exam_detail_list = paginator.page(paginator.num_pages)    
        '''以下是错误的
        data=[]
        for exam_detail in exam_detail_list:
            
            data.append(ExamDetailSerializer(exam_detail).data)
        print(data)
        '''
        data=ExamDetailSerializer(exam_detail_list, many=True).data
        return self.success(data={"data":data, "total":paginator.count})
        
        


'''
admin/exam/exam_detail/update
'''            
class ExamDetailUpdate(APIView):
    """
    更新考试题目信息
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        exam_detail_id = data.get('id')
        if not exam_detail_id:
            return self.error("exam_detail_id is required")
        try:
            exam_detail = ExamDetail.objects.get(id=exam_detail_id)
        except ExamDetail.DoesNotExist:
            return self.error("exam_detail not found")
        exam_detail.name = data.get('name', exam_detail.name)
        exam_detail.desc = data.get('desc', exam_detail.desc)
        exam_detail.enable = data.get('enable', exam_detail.enable)
        problems = data.get('problems')
        #将problems中的题目id和分数提取出来
        if problems:
            exam_detail.problems = [{"id": problem["problem"]["id"], "score": problem["score"]} for problem in problems]
        else:
            exam_detail.problems = []
        exam_detail.save()
        return self.success(data=exam_detail.id)

'''
admin/exam/exam_detail/delete
'''
class ExamDetailDelete(APIView):
    """
    删除考试题目
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        exam_detail_id = data.get('id')
        if not exam_detail_id:
            return self.error("exam_detail_id is required")
        try:
            exam_detail = ExamDetail.objects.get(id=exam_detail_id)
            exam_detail.delete()
            return self.success(data=exam_detail.id)
        except ExamDetail.DoesNotExist:
            return self.error("exam_detail not found")

'''
admin/exam/result/get
'''
class ExamResultGet(APIView):
    @admin_role_required
    def get(self, request):
        """
        获取某场考试成绩
        """
        exam_id = request.GET.get('exam_id')
        if not exam_id:
            return self.error("exam_id is required")
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return self.error("exam not found")
        exam_result = ExamResult.objects.filter(exam=exam).values()
        if not exam_result:
            return self.error("exam_result not found")
        exam_result = exam_result[0]
        exam_result['answers'] = exam_result['answers']
        exam_result['total_score'] = exam_result['total_score']
        exam_result['exam'] = exam.id
        return self.success(data=exam_result)

'''
admin/exam/result/get_list
'''
class ExamResultList(APIView):
    """
    获取所有考试成绩
    """
    @admin_role_required
    def get(self, request):
        """
        获取所有考试成绩
        """
        exam_results = ExamResult.objects.all().values()
        return self.success(data=list(exam_results))

'''
admin/student/create
'''
class StudentCreate(APIView):
    """
    创建学生
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        #默认用户名和密码就是学号
        username=data.get('sid')
        
        user = self.create_user(username=username, email=data.get('email'), is_student=True)
        #通过学号sid检查学生是否已经存在
        if StudentProfile.objects.filter(sid=data.get('sid')).exists():
            return self.error("Student with this SID already exists")
        
        student_profile = StudentProfile.objects.create(
            user=user,
            name=data.get('name'),
            sid=data.get('sid'),
            s_class=data.get('s_class'),
            profession=data.get('profession'),
            sub_college=data.get('sub_college'),
            enable=data.get('enable', True),
        )
        student_profile.save()
        return self.success(data=student_profile.id)
    def create_user(self, username, email, is_student=False):
        """
        创建用户
        """
        #先检查是否已经存在该用户，如果存在，直接返回User对象，否则创建
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username)
        user = User.objects.create(username=username, email=email)
        if is_student:
            user.admin_type = AdminType.REGULAR_USER
        else:
            user.admin_type = AdminType.ADMIN
        user.set_password(username)  # 默认密码为用户名
        user.save()
        UserProfile.objects.create(user=user)
        return user

'''
admin/student/get
'''
class StudentGet(APIView):
    @admin_role_required
    def get(self, request):
        """
        获取某个学生信息
        """
        student_id = request.GET.get('id')
        if not student_id:
            return self.error("student_id is required")
        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return self.error("student not found")
        student_data = {
            'id': student.id,
            'name': student.name,
            'sid': student.sid,
            's_class': student.s_class,
            'profession': student.profession,
            'sub_college': student.sub_college,

        }
        return self.success(data=student_data)

'''
admin/student/get_list
'''
class StudentList(APIView):
    """
    获取所有学生信息
    """
    @admin_role_required
    def get(self, request):
        """
        获取所有学生信息
        """
        page_index=request.GET.get('page_idx', 1)
        page_size=request.GET.get('nums_per_page', 10)
        keyword=request.GET.get('keyword') #学号
        students=StudentProfile.objects.order_by("-create_time")
        if keyword!=None:
            students = students.filter(
                Q(name__icontains=keyword) | Q(sid__icontains=keyword)
                )
        paginator = Paginator(students, page_size)  # 每页显示 10 条记录
        try:
            student_list = paginator.page(page_index)
        except PageNotAnInteger:
            # 如果页码不是一个整数，则返回第一页的结果
            student_list = paginator.page(1)
        except EmptyPage:
            # 如果页码超出了最大页数，则返回最后一页的结果
            student_list = paginator.page(paginator.num_pages)    

        data=StudentSerializer(student_list, many=True).data
        return self.success(data={"data":data, "total":paginator.count})

'''
admin/student/update
'''
class StudentUpdate(APIView):
    """
    更新学生信息
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        student_id = data.get('id')
        if not student_id:
            return self.error("student_id is required")
        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return self.error("student not found")
        student.name = data.get('name', student.name)
        student.sid = data.get('sid', student.sid)
        student.s_class = data.get('s_class', student.s_class)
        student.profession = data.get('profession', student.profession)
        student.sub_college = data.get('sub_college', student.sub_college)
        student.enable = data.get('enable', student.enable)

        student.save()
        return self.success(data=student.id)

'''
admin/student/delete
'''
class StudentDelete(APIView):
    """
    删除学生
    """
    @admin_role_required
    def get(self, request):
        data = request.data
        student_id = data.get('id')
        if not student_id:
            return self.error("student_id is required")
        try:
            student = StudentProfile.objects.get(id=student_id)
            #学号就是用户名
            user=User.objects.get(username=student.sid)
        except StudentProfile.DoesNotExist:
            return self.error("student not found")
        student.delete()
        if user:
            # if user.profile:
            #     user.userprofile.delete()
            user.delete()
        return self.success(data=student.id)

    def error(self, message):
        """
        返回错误信息
        """
        return {
            'status': 'error',
            'message': message
        }
    
class StudentResetPassword(APIView):
    """
    重置学生密码
    """
    @admin_role_required
    def post(self, request):
        data = request.data
        student_id = data.get('id')
        if not student_id:
            return self.error("student_id is required")
        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return self.error("student not found")
        #重置密码为学号
        student.user.set_password(student.sid)
        student.user.save()
        return self.success(data=student.id)


'''
admin/student/import
'''
# class MySerializer(serializers.Serializer):
#     file = serializers.FileField()
@method_decorator(csrf_exempt, name='dispatch')
class StudentImport(APIView):
    parser_classes=[MultiPartParser,FormParser]
    """
    批量导入学生
    接受上传的xlsx文件，并根据文件内容创建学生用户
    文件格式为：
    学院，专业，班级，学号，姓名，密码
    """
    
    @admin_role_required
    def post(self, request):
        
        # form=serializers.FileUploadForm(request.POST, request.FILES)
        # uploaded_file = form.file
        uploaded_file=request.FILES.get('file')
        if not uploaded_file:
            return self.error("file is required")
        # 检查文件类型
        if not uploaded_file.name.endswith('.xlsx'):
            return self.error("only .xlsx files are allowed")

        try:
            df=pd.read_excel(BytesIO(uploaded_file.read()),sheet_name=0)
            sub_college_data= df['学院']  
            profession_data= df['专业']
            s_class_data= df['班级']
            sid_data= df['学号']
            name_data= df['姓名']
            password_data= df['密码'].astype(str)  # 确保密码是字符串类型
            #跟踪记录每一行记录导入成功还是失败，失败会添加原因，其行索引应该和df一致
            result_data =pd.Series() 
            reason_data=pd.Series() 
            students = []
            for row in zip(sub_college_data, profession_data, s_class_data, sid_data, name_data, password_data,df.index):
                
                sub_college, profession, s_class, sid, name, password,index = row
                result_data.at[index] = '成功'
                if not sid or not name:
                    result_data.at[index] = '失败'
                    reason_data.at[index] = '学号或姓名不能为空'
                    continue
                # 检查学号是否已存在
                if StudentProfile.objects.filter(sid=sid).exists():
                    result_data.at[index] = '失败'
                    reason_data.at[index] = '学号已存在'
                    continue
                if password=="" or pd.isna(password):
                    password=sid
                user = self.create_user(username=sid,password=password, is_student=True)
                
                students.append(StudentProfile(user=user, name=name, sid=sid, s_class=s_class, profession=profession, sub_college=sub_college))
            StudentProfile.objects.bulk_create(students)
            df['导入结果']=result_data
            df['失败原因']=reason_data
            # #这里返回导入结果文件
            # from io import BytesIO
            # output = BytesIO()
            # df.to_excel(output, index=False)
            # output.seek(0)
            # response = Response(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            # response['Content-Disposition'] = 'attachment; filename="学生信息导入结果.xlsx"'
            # return response
            #保存excel文件到服务器，命名添加时间信息
            filename="导入学生信息_"+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+".xlsx"
            save_path=os.path.join(settings.UPLOAD_DIR, filename)
            df.to_excel(save_path, index=False)
            #这里的url_path是/api/student/import?filename=xxx。
            url_path=f"/admin/student/import?filename={filename}"
            
            return self.success(data={'url': f"{url_path}", 'message': '导入完成，点击链接下载导入结果文件'})
            
        except Exception as e:
            print(e)
            return self.error(str(e))

    
    @admin_role_required
    def get(self, request):
        '''
        返回客户端想下载的文件
        '''
        filename = request.GET.get('filename')
        if not filename:
            return self.error("filename is required")
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            return self.error("file not found")
        
        # 使用 FileResponse 直接返回文件
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        response['Content-Disposition'] = f'attachment; filename=import_result.xlsx'
        return response
    def create_user(self, username, password, is_student=False):
        """
        创建用户
        """
        #先检查是否已经存在该用户，如果存在，直接返回User对象，否则创建
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username)
 
        user = User.objects.create(username=username)
        if is_student:
            user.admin_type = AdminType.REGULAR_USER
        else:
            user.admin_type = AdminType.ADMIN
        user.set_password(password)  # 设置密码
        user.save()
        UserProfile.objects.create(user=user)
        return user


        
class StudentExamResultHistoryAPI(APIView):
    '''
    获取一个学生的所有历史考试数据
    '''
    @login_required
    def get(self, request):
        page_index = request.GET.get("page",1)
        page_size = request.GET.get("limit",10)
        student_id = request.GET.get("student_id")
        if not student_id:
            return self.error("student_id is needed")
        
        exam_results = ExamResult.objects.filter(student_id=student_id).select_related("exam").order_by("-create_time")
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