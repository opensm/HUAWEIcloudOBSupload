if [ $# -ne 7 ];then
  echo "$0 \${WORKSPACE} \${name} \${page} \${code} \${FORCE_UPDATE} \${TASKTIME} \${version_path} "
  exit 1
fi
if [ ! -d "${1}" ];then
   echo "${1}，目录不存在！"
   exit 1
fi
cd "${1}" || exit 1
if [ ! -f "./notice.json" ];then
    echo "APPStore更新必须更新notice.json"
    exit 1
fi
if [ $7 == "dev" ];then
  bucket="tongyichelianwang-dev"
elif [ $7 == "test" ]; then
  bucket="tongyichelianwang-test"
elif [ $7 == "prod" ]; then
  bucket="chelianwang-prod"
else
  echo "输入参数错误，请检查！"
  exit 1
fi

COS_PATH="tsp-ios"
if [ ! -d "${1}/${COS_PATH}" ];then
  mkdir -pv "${1}/${COS_PATH}" || exit 1
fi
ZIP_PACKAGE=$(date "+%Y%m%d%H%M%S")_"${2}"_"${6}"_"$bucket".zip
echo -e "{\"name\":\"${2}\",\"date\":\"$(date "+%Y%m%d")\",\"code\":${4},\"mustUpgrade\":${5}}" > "${1}/${COS_PATH}"/version.json
if [ $? -ne 0 ];then
  echo "${1}/version.json 生成失败！"
  exit 1
fi
echo -e "var IOS_VERSION_CONFIG = {'name':'${2}','date':'$(date '+%Y%m%d')','code':'${4}','mustUpgrade':'${5}'}" > "${1}/${COS_PATH}"/version.js
if [ $? -ne 0 ];then
  echo "${1}/version.js 生成失败！"
  exit 1
fi
mv notice.json "${1}/${COS_PATH}" || exit 1
zip -r ./"${ZIP_PACKAGE}" "${COS_PATH}"
if [ "$?" -ne 0 ];then
   echo "打包文件：${ZIP_PACKAGE},失败！"
   exit 1
fi