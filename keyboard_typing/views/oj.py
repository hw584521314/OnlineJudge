

from utils.api.api import APIView
from ..models import TypingHistory
from account.decorators import login_required
from utils.api import  serializers
class TypingHistorySerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 格式化输出
    class Meta:
        model = TypingHistory
        fields = "__all__"

class TypingHistoryView(APIView):
    @login_required
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return self.success()
        #从url参数获取username
        #print(request.GET)
        username = request.GET.get("username")
        #返回用户的打字记录数据
        if username:
            data=TypingHistory.objects.filter(user__username=username).order_by("create_time").all()
        else:
            uid=request.user.id
            data=TypingHistory.objects.filter(user__id=uid).order_by("create_time").all()
        #uid=request.user.id
        print(username,data)
        data=TypingHistorySerializer(data, many=True).data if data else []
        return self.success(data)


class TypingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TypingHistory
        fields = ["accuracy","tpm"]

class Typing(APIView):
    @login_required
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return self.success()
        
        username = request.GET.get("username")
        if username:
        #返回用户的打字最好数据
        #
            data=TypingHistory.objects.filter(user__username=username).order_by("-accuracy","-tpm").first()
        else:
            uid=request.user.id
            data=TypingHistory.objects.filter(user__id=uid).order_by("-accuracy","-tpm").first()
        
        #print(username,data)
        data=TypingSerializer(data).data if data else {"accuracy":0.0,"tpm":0}
        return self.success(data)
    
    @login_required
    def post(self, request):
        #获取accuracy，tpm，total_hit，error_hit，practice_munites
        accuracy = request.data.get("accuracy", 0.0)
        tpm = request.data.get("tpm", 0.0)
        total_hit = request.data.get("total_hit", 0)
        error_hit = request.data.get("error_hit", 0)
        practice_munites = request.data.get("practice_munites", 0.0)
        user = request.user
        #存入数据库
        TypingHistory.objects.create(user=user, accuracy=accuracy, tpm=tpm, total_hit=total_hit, error_hit=error_hit, practice_munites=practice_munites)
        return self.success("提交成功")