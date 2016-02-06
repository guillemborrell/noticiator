import os
import webapp2
import jinja2
import datetime
from google.appengine.api import search
from google.appengine.ext import ndb
from google.appengine.api import users

AUTHORIZED_USERS = ['guillemborrell@gmail.com',
                    'beatriz88rc@gmail.com']

class IndexedDocument(ndb.Model):
    """Models an individual Document entry with key and date."""
    doc_id = ndb.StringProperty()
    title = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def check_user(user):
    if user:
        if user.email() in AUTHORIZED_USERS:
            return user, users.create_logout_url('/')

        else:
            return False, False

    else:
        return False, False


class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}

        if self.request.get('query'):
            query = self.request.get('query')
            template_values['query'] = query
            template_values['count'] = 20
            index = search.Index('myIndex')

            try:
                if self.request.get('count'):
                    count = int(self.request.get('count'))
                    template_values['count'] = int(count + 20)
                    options = search.QueryOptions(offset=count)
                    query = search.Query(query_string=query,
                                         options=options)
                    results = index.search(query)

                else:
                    results = index.search(query)

                template_values['matches'] = results.number_found
                template_values['documents'] = results.results
                template_values['numdocuments'] = len(
                    template_values['documents'])


            except search.Error:
                logging.exception('Search failed')

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class DocumentPage(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        doc_id = self.request.get('doc_id')
        index = search.Index('myIndex')
        
        template_values['document'] = index.get(doc_id)
        template = JINJA_ENVIRONMENT.get_template('document.html')
        self.response.write(template.render(template_values))



class NewPage(webapp2.RequestHandler):
    def get(self):
        user, logout = check_user(users.get_current_user())
        if user:
            template_values = {'logout':logout}
            template = JINJA_ENVIRONMENT.get_template('new.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url('/new'))

    def post(self):
        user, logout = check_user(users.get_current_user())
        if user:
            title = self.request.get('title')
            date = datetime.datetime.strptime(self.request.get('date'),'%d/%m/%Y')
            body = self.request.get('body')
            newspaper = self.request.get('newspaper')
            keywords = self.request.get('keywords')
            industry = self.request.get('industry')
            region = self.request.get('region')
            
            document = search.Document(
                fields = [search.TextField(name='title', value=title),
                          search.DateField(name='date',  value=date),
                          search.AtomField(name='newspaper', value=newspaper),
                          search.TextField(name='body', value=body),
                          search.TextField(name='keywords', value=keywords),
                          search.TextField(name='industry', value=industry),
                          search.TextField(name='region', value=region)
                          ]
                )
            
            try:
                index = search.Index(name="myIndex")
                results = index.put(document)
                doc_id = results[0].id
                indexed_document = IndexedDocument(doc_id = doc_id,
                                                   title = title)
                indexed_document.put()
            
            except search.Error:
                logging.exception('Document insertion failed')
                
        self.redirect('/new')


class EditPage(webapp2.RequestHandler):
    def get(self):
        user, logout = check_user(users.get_current_user())
        doc_id = self.request.get('doc_id')
        if user:
            index = search.Index('myIndex')
            document = index.get(doc_id)
            template_values = {
                'logout': logout,
                'doc_id':doc_id,
                'title':document.fields[0].value,
                'date':document.fields[1].value,
                'newspaper':document.fields[2].value,
                'body':document.fields[3].value,
                'keywords':document.fields[4].value,
                'industry':document.fields[5].value,
                'region':document.fields[4].value}
            
            template = JINJA_ENVIRONMENT.get_template('edit.html')
            self.response.write(template.render(template_values))

        else:
            self.redirect(users.create_login_url(
                '/edit?doc_id={}'.format(doc_id)
            ))

    def post(self):
        user, logout = check_user(users.get_current_user())
        if user:
            doc_id = self.request.get('doc_id')            
            method = self.request.get('method')

            if method == 'post':
                title = self.request.get('title')
                date = datetime.datetime.strptime(self.request.get('date'),
                                                  '%d/%m/%Y')
                body = self.request.get('body')
                newspaper = self.request.get('newspaper')
                keywords = self.request.get('keywords')
                industry = self.request.get('industry')
                region = self.request.get('region')
                
                document = search.Document(
                    doc_id = doc_id,
                    fields = [search.TextField(name='title', value=title),
                              search.DateField(name='date',  value=date),
                              search.AtomField(name='newspaper', value=newspaper),
                              search.TextField(name='body', value=body),
                              search.TextField(name='keywords', value=keywords),
                              search.TextField(name='industry', value=industry),
                              search.TextField(name='region', value=region)
                              ]
                    )
                
                try:
                    index = search.Index(name="myIndex")
                    results = index.put(document)
    
                except search.Error:
                    logging.exception('Document edition failed')

            if method == 'delete':
                try:
                    index = search.Index(name="myIndex")
                    results = index.delete(doc_id)
                    
                except search.Error:
                    logging.exception('Document {} deletion failed'.format(doc_id))
                
        self.redirect('/new')

    def delete(self):
        user, logout = check_user(users.get_current_user())
        if user:
            doc_id = self.request.get('doc_id')
            
        self.redirect('/new')


application = webapp2.WSGIApplication([
        ('/', MainPage),
        ('/new', NewPage),
        ('/edit', EditPage),
        ('/document', DocumentPage),
        ], debug=True)

