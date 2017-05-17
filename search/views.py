from django.shortcuts import render
from django.views.generic.base import View
from search.models import Post
from django.http import HttpResponse
import json
from datetime import datetime
import MySQLdb
import math

from elasticsearch import Elasticsearch

es_client = Elasticsearch(hosts=['127.0.0.1'])


# Create your views here.
class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        re_data = []
        if key_words:
            s = Post.search()
            s = s.suggest("my_suggest", key_words, completion={
                "field": "suggest",
                "fuzzy": {
                    "fuzziness": 1,
                },
                "size": 10
            })
            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_data.append(source["title"])
        return HttpResponse(json.dumps(re_data), content_type="application/json")


class SearchView(View):
    def get(self, request):
        begin_time = datetime.now()
        key_words = request.GET.get('q', '')
        page = request.GET.get('p',1)
        s_type = request.GET.get('s_type','jobbole')
        if s_type=='article':
            s_type='jobbole'
        try:
            page = int(page)
        except:
            page = 1
        response = es_client.search(
            index=s_type,
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["tags", "title", "content"]
                    }
                },
                "from": page,
                "size": 10,
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "title": {},
                        "content": {}
                    }
                }
            }
        )

        total_num = response["hits"]["total"]
        hit_list = []
        for hit in response['hits']['hits']:
            hit_dict = {}
            if "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = hit["_source"]["title"]
            if "content" in hit["highlight"]:
                hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]
            else:
                hit_dict["content"] = hit["_source"]["content"][:500]
            hit_dict["post_at"] = hit["_source"]["post_at"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]

            hit_list.append(hit_dict)

        db = MySQLdb.connect("localhost", "root", "root", "spiders")
        cursor = db.cursor()
        cursor.execute("SELECT count(*) from jobbole_articles")
        jobbole_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) from zhihu_questions")
        zhihu_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) from lagou_jobs")
        lagou_count = cursor.fetchone()[0]
        return render(request, "result.html",{
            "all_hits":hit_list,
            "key_words":key_words,
            "page":page,
            "total_num":total_num,
            'duration':(datetime.now()-begin_time).total_seconds(),
            'jobbole_count':jobbole_count,
            'zhihu_count':zhihu_count,
            'lagou_count':lagou_count,
            'page_nums':math.ceil(total_num/10)
        })

