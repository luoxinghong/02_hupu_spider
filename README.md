# hupu_spider
用scrapy框架写了一个爬取虎扑步行街帖子的爬虫
步行街地址：
https://bbs.hupu.com/bxj

### 目前完成功能
1. 爬取帖子，获取作者，发帖时间，帖子浏览数，回帖数等信息存到数据库中
2. 爬取帖子内容，获取回帖的数据并插入到数据库中

### 待完善
1. 随机切换user-agent.目前没有设置user-agent，虎扑估计没怎么做反爬，所以目前没遇到什么问题。但是为了避免将来爬虫突然失效，还是做一下user-agent设置比较稳妥
2. 添加代理，防止ip被封



当需要的软件和库都安装好后，进行以下步骤
1. 进入mysql环境，创建数据库。`create database hupu`。当然，数据库不叫虎扑也可以，到时记得改项目中的配置文件
2. 执行该项目中的 `mysql_db/hupu_post.sql` 创建相关的表。
3. 修改`db_config.py`中的数据库配置。包括用户密码，数据库等。
4. 执行`./run.sh`运行程序，window环境下直接在hupu_spider目录下执行 `scrapy crawl hupu_post` 也是一样的。
