from django.db import models
from django.conf import settings
from visionar.config import environment
from django.contrib.auth.models import User
from visionar.utils.baseconvert import BASE10, BASE62, baseconvert
from easy_thumbnails.fields import ThumbnailerImageField
import json
import os

def templates_file_upload(instance, filename):
    _, ext = os.path.splitext(filename)
    format =  str(instance.name) + ext
    return os.path.join("templates_blender", format)

def media_file_upload(instance, filename):
    path = "projects/" + instance.project.urlhash
    return os.path.join(path, filename)	

class Tag(models.Model):
	word = models.CharField(max_length=35)
	
	def __unicode__(self):
		return self.word
	
	class Admin:
		pass

class Template(models.Model):
	filename = models.CharField(max_length=100)
	name = models.CharField(max_length=50, unique=True)
	legend = models.CharField(max_length=100, unique=True)
	tags = models.ManyToManyField(Tag)
	thumb = ThumbnailerImageField(upload_to=templates_file_upload)
	preview = models.FileField(upload_to=templates_file_upload)
	image_number = models.IntegerField()
	text_number = models.IntegerField()
	
	def __unicode__(self):
		return self.name

	@property
	def thumbnail(self):
		return self.thumb['380'].url
	
	class Admin:
		pass

class RenderState(models.Model):
	name = models.CharField(max_length=50)
	description = models.CharField(max_length=250)

	class Admin:
		pass
	
	def __unicode__(self):
		return self.name

class RenderType(models.Model):
	name = models.CharField(max_length=50)
	description = models.CharField(max_length=250)

	class Admin:
		pass

	def __unicode__(self):
		return self.name
		
class Project(models.Model):

	REVISION_STATES_CHOICES = (
		('PENDING', 'Pendiente'),
		('OBSERV', 'En Observacion'),
		('REJECTED', 'Rechazado por Inapropiado'),
		('ACCEPTED', 'Aceptado')
	)

	user = models.ForeignKey(User)
	template = models.ForeignKey(Template)
	urlhash = models.CharField(max_length=50 ,unique=True)
	title = models.CharField(max_length=200, default="Sin Titulo")
	created = models.DateTimeField(auto_now_add=True, verbose_name = 'fecha de creacion')
	modified = models.DateTimeField(auto_now_add=True, verbose_name = 'fecha de modificacion')
	urlrender = models.CharField(max_length=500, null=True)
	state = models.ForeignKey(RenderState)
	positions = models.CharField(max_length=500)
	texts = models.CharField(max_length=1000)
	revision_state = models.CharField(max_length=10,choices=REVISION_STATES_CHOICES)

	class Admin:
		pass

	def __unicode__(self):
		return self.title

	def getImagesPath(self):
		if environment.MEDIA_HOST:
			return os.path.join(environment.MEDIA_HOST, 'projects', self.urlhash + '/')
		else:
			return os.path.join(environment.HOST, 'media/projects', self.urlhash + '/')

	@property
	def thumb(self):
		media = Media.objects.filter(project=self).filter(mediatype=Mediatype.objects.get(typename="Image"))	
		if media:
			return media[0].image.file['380'].url
		else:
			return 	os.path.join(settings.STATIC_URL, 'visionar/images/no-image.jpg')

	def save(self):
		super(Project, self).save()

		if not self.urlhash:
			self.urlhash = baseconvert('100' + str(self.id),BASE10,BASE62)
			self.save()  


class Mediatype(models.Model):
	typename = models.CharField(max_length=200)

	def __unicode__(self):
		return self.typename
	class Admin:
		pass

class Media(models.Model):
	mediatype = models.ForeignKey(Mediatype)
	project = models.ForeignKey(Project)
	
	def __unicode__(self):
		return self.mediatype.typename

	@property	
	def position(self):
		#p = json.dumps(self.project.positions)
		p = Project.objects.get(id=self.project.id)
		positions = json.loads(p.positions)
		convert = [ int(x) for x in positions ]
		return convert.index(self.id)


class Text(Media):
	text = models.CharField(max_length=500)

class Image(Media):
	file = ThumbnailerImageField(upload_to=media_file_upload)

	@property
	def thumb(self):
		return self.file['avatar'].url
