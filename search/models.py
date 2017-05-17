from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text,Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

connections.create_connection(hosts=["localhost"])

#弥补es_dsl代码缺陷
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}
ik_analyzer = CustomAnalyzer("ik_max_word",filter=['lowercase'])


class Post(DocType):
    #es_dsl的代码Competion貌似有缺陷不能直接写参数
    suggest = Completion(analyzer=ik_analyzer, search_analyzer=ik_analyzer)

    url = Keyword()
    title = Text(analyzer="ik_max_word")
    post_at = Date()
    like_num = Integer()
    fav_num = Integer()
    comments_num = Integer()
    post_thumb = Keyword()
    thumb_path = Keyword()
    content = Text(analyzer="ik_max_word")
    tags = Text(analyzer="ik_max_word")

    class Meta:
        index="jobbole"
        doc_type="articles"

if __name__ == "__main__":
    Post.init()