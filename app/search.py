from flask import current_app

def add_to_index(index, model):
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)

def remove_from_index(index, model):
    current_app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, field='username', amount=10):
    search = current_app.elasticsearch.search(
        index=index,
        body=
        {
            'size': amount,
            'query':            
            {
                'bool':
                {
                    'should':
                    [
                    {
                        'fuzzy': 
                        {
                            field: 
                            {
                                'value': query,
                                'fuzziness': 5
                            }   
                        }
                    },
                    {
                        'prefix':
                        {
                            f'{field}.keyword': query
                        }
                    }
                    ]
                }
            },
        }
    )
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
