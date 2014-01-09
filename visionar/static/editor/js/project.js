$(document).ready(function() {
	
	var Project = function(text){
		this.urlhash = $(location).attr('pathname').split('/')[2];
		this.text = text;
		this.imageCount = 0;
		this.imageNumber = 0;
		this.init();
	}

	Project.prototype.init = function(){
		this.imageCount = _TEMPLATE_IMAGE_COUNT
		this.imageNumber = _TEMPLATE_IMAGE_NUMBER

		this.setUploader();
		var self = this;
		
		$("#render").click(function(){
			self.render();
		})

		$("#delete-media").click(function(){
			var entry = $($(".entry-selected")[0]);
			if(entry.hasClass("entry-text")){
				self.text.deleteText(entry);
			}else{
				self.deleteMedia();
			}
			
		});


		$("#save-project").click(function(){
			self.save();
		})

		$("#save-title").click(function(){
			self.saveTitle();
		})

		$(".change-media").each(function(i, v){
			$(v).click(function(){
				self.changeMedia($(this));
			})
		});
/*
		$("#add-text").click(function(){

		})*/  
		this.resetDragDrop();
		this.disableFileInputDrag();
		this.setSelectEvent();
		if(this.imageCount >= this.imageNumber){
			this.disableAddImage();
		}
	}

	Project.prototype.saveTitle = function(){
		var self = this;
		$.ajax({
	    	url: "/project/saveTitle/",
	       	type: 'POST',
	       	data: {
	       		project: self.urlhash,
	       		user: _USER,
	       		title: $("#change-title-field").val(),
	       		csrfmiddlewaretoken: _csrftoken

	       	},
	        success: function(data, status, xhr) {
	        	if(data.response){
	        		$("#project-title").html($("#change-title-field").val())
	        	}
	        },
	        error: function(xhr, errmsg, err){
	    		console.log(errmsg);
	        	console.log(xhr);
	        	console.log(err);
	        }
	  	})
	}

	Project.prototype.setSelectEvent = function(){
		var self = this;
		$(".entry-filled").each(function(i,v){
			$(v).click(function(){
				self.setOnClick(this)
			});
		})
	}
	
	Project.prototype.uploadLoading = function(e){
		var element = $(e)
		element.css("display", "none")
		element.siblings().css("display", "none")
		element.parent().append("<h4>Loading...</h4>")
		element.parent().removeAttr('data-mediatype')
	}

	Project.prototype.newFileField = function(){
		this.imageCount++;
		var entry = "<div data-mediatype='Imagen' class='entry'>" +
						"<h4><span id='image-number'>"+this.imageCount+ "</span>/" + this.imageNumber+"</h4>" +
						"<input type='file' />" +
						"<h3 class='file-input-inside'><i class='icon-large icon-camera'></i>Agregar Imagen</h3>" +
					"</div>"

		$($(".hippster")[0]).append(entry);
	}
	
	Project.prototype.getPositions = function(){
		var positions = [];
		$(".hippster .ss-active-child").each(function(i,v){
			positions[$(this).index()] = $(this).data('id');
		});
		return positions;
	}

	Project.prototype.disableFileInputDrag = function(){
		var p = $("input[type=file]").parent();
		p.removeClass('ss-active-child');
	}

	Project.prototype.setContentOnUpload = function(e, d){
		var self = this;
		var div = $(e).parent();
		div.addClass("entry-filled");
		div.data('id', d.id); 
		div.html('<img data-id="'+d.id+'" src="'+ d.thumb +'"/>');
		div.click(function(){
			self.setOnClick(this)
		});
	}
	
	Project.prototype.resetDragDrop = function(){
		$(".hippster").trigger("ss-rearrange")
		$(".hippster").shapeshift({
		    minColumns: 3,
		    enableCrossDrop: false,
		    align: "left"
		});
	}
	
	Project.prototype.setOnClick = function(obj){
		$(".entry-selected").each(function(i,v){
			if(!$(obj).is(this)){
				$(this).removeClass("entry-selected");
			}
		})
		$(obj).toggleClass("entry-selected");
	}
	
	Project.prototype.logErrors = function(xhr,errmsg, err){
		console.log(errmsg);
		console.log(xhr);
		console.log(err);
	}	       

	Project.prototype.setUploader = function(){
		var self = this;
		this.uploader = new Uploader("/project/uploadImage/", {
			data:{
				project: self.urlhash,
			},
			
			onChange : function(i){
				self.uploadLoading(i);
				
			},
			success: function(d, i){
				self.newFileField();
				self.disableFileInputDrag();
				self.uploader.init();
				self.setContentOnUpload(i,d);
				self.resetDragDrop();
				self.disableFileInputDrag();
				if(self.imageCount >= self.imageNumber){
					self.disableAddImage()
				}
			},
			error: this.logErrors,
		});
	}
	
	Project.prototype.save = function(){
		var self = this;
		$.ajax({
	    	url: "/project/save/",
	       	type: 'POST',
	       	data: {
	       		project: self.urlhash,
	       		user: _USER,
	       		images: JSON.stringify(self.getPositions()),
	       		texts: JSON.stringify(self.text.getPositions()),
	       		csrfmiddlewaretoken: _csrftoken

	       	},
	        success: function(data, status, xhr) {
	        	if(data.response){
	        		$('#save-project-tag').fadeOut(500, function() {
				        var self = this;
				        var text = $(this).text();
				    	$(this).text('Proyecto guardado con exito!').fadeIn(500);
				        $('#close-save-project').click(function(){
				        	$(self).text(text)
				        	console.log(text)
				        })
				    });
	        	}
	        },
	        error: function(xhr, errmsg, err){
	    		/*console.log(errmsg);
	        	console.log(xhr);
	        	console.log(err);*/
	        }
	  	})
	}

	Project.prototype.render = function(){
		var self = this;
		$("#video").html("Loading....");
		$.ajax({
	    	url: "/project/render/",
	       	type: 'POST',
	       	data: {
	       		project: self.urlhash,
	       		user: _USER,
	       		csrfmiddlewaretoken: _csrftoken
			},
	        success: function(data, status, xhr) {
	       		console.log(data)
	       		setTimeout(function(){
	       			self.askPreview();
	       		}, 1000)
	       		//self.createVideo(data.response);
	        },
	        error: self.logErros,
	    }); 
	}

	Project.prototype.deleteMedia = function(){
		var self = this;
		if($(".entry-selected")[0]){
			if($(".entry-selected")[0])
			var entry = $($(".entry-selected")[0]);
			$.ajax({
		    	url: "/project/deleteMedia/",
		       	type: 'POST',
		       	data: {
		       		media: entry.data("id"),
		       		csrfmiddlewaretoken: _csrftoken
				},
		        success: function(data, status, xhr) {
		       		entry.remove();
		       		self.imageCount--;
		       		$("#image-number").html(self.imageCount);
		       		$(".hippster").trigger("ss-rearrange");
		       		self.resetDragDrop();
		       		self.disableFileInputDrag();
		        },
		        error: self.logErrors,
		    }); 
		}
	}

	Project.prototype.createVideo = function(urls){
		var self = this;
		$("#video").html("<video id='video-preview' class='video-js vjs-default-skin' width='650' height='400' preload='auto' controls>  <source src='"+urls.webm+"' type='video/webm'> <source src='"+urls.mp4+"' type='video/mp4'> <source src='"+urls.ogg+"' type='video/ogg'></video>")
		videojs("video-preview", {}, function(){
  			// Player (this) is initialized and ready.
		}).on("ended", function(){this.src({ type: "video/webm", src: urls.webm });});
		//myPlayer.on("ended", function () { this.src({ type: "video/mp4", src: URL }); });
	}

	Project.prototype.changeMedia = function(e){
		
		var html = "<i class='icon-large icon-"+e.data("icon")+"'></i>Agregar " + e.data("type")
		$($(".file-input-inside")[0]).html(html);
		var parent = $($(".file-input-inside")[0]).parent()
		parent.data('mediatype', e.data("type"))
		parent.attr('data-mediatype', e.data("type"))

	}

	Project.prototype.getPreview = function(interval){
		var self = this;
		$.ajax({
		    	url: "/project/getPreview/",
		       	type: 'POST',
		       	data: {
		       		project: self.urlhash,
		       		csrfmiddlewaretoken: _csrftoken
				},
		        success: function(data, status, xhr) {
		       		if(data.response != "PENDING"){
		       			console.log(JSON.parse(data.response))
		       			self.createVideo(JSON.parse(data.response));
		       			clearInterval(interval);
		       		}
		        },
		        error: self.logErrors,
		    }); 
	}

	Project.prototype.disableAddImage = function(){
		var p = $("input[type=file]").parent();
		$("input[type=file]").prop('disabled', true);
	}

	Project.prototype.askPreview = function(){
		var self = this;
		var interval = setInterval(function(){
			self.getPreview(interval);
		}, 10000)
	}

	var TextManager = function(){
		this.fields = [];
		this.textCount = 0;
		this.textNumber = 0;
		this.init();
	}

	TextManager.prototype.init = function(){
		this.textCount = parseInt(_TEMPLATE_TEXT_COUNT);
		this.textNumber = parseInt(_TEMPLATE_TEXT_NUMBER);
		this.urlhash = $(location).attr('pathname').split('/')[2];

		$(".shift-text").shapeshift({
		    minColumns: 3,
		    enableCrossDrop: false,
		    dragWhitelist: ".dragable",
		    align: "left",
		});
		var self = this;
		$("#add-text-button").click(function(){
			self.addTextPane();
		})
		$("#add-text").removeClass('ss-active-child');
		$("#add-text-popup").removeClass('ss-active-child');

		$("#add-text").click(function(){
			$("#add-text-field").val("");
		})

		$(".entry-text").each(function(i,v){
			$(this).click(function(){
				self.setOnClick(this)
			})
			
		})
		$("#add-text-number").html(this.textCount);

		if(this.textCount >= this.textNumber){
			this.disableAddText();
		}
	}

	TextManager.prototype.saveText = function(){
		var currentText = $("#add-text-field").val();
		this.textCount++;
		$("#add-text-number").html(this.textCount); 
		this.fields.push(currentText)
		return currentText;
	}

	TextManager.prototype.createPane = function(val){
		var pane = $("<div class='entry entry-text dragable' data-text='"+ val +"'><p>" + val + "</p></div>")
		$("#add-text").before(pane)
		return pane;
	}

	TextManager.prototype.sendToServer = function(){
		var self = this;
		$.ajax({
	    	url: "/project/save/",
	       	type: 'POST',
	       	data: {
	       		project: self.urlhash,
	       		user: _USER,
	       		texts: JSON.stringify(self.getPositions()),
	       		csrfmiddlewaretoken: _csrftoken
			},
	        success: function(data, status, xhr) {
	        	
	        },
	        error: function(xhr, errmsg, err){
	    		console.log(errmsg);
	        	console.log(xhr);
	        	console.log(err);
	        }
	  	})
	}

	TextManager.prototype.getPositions = function(){
		var positions = [];
		$(".shift-text .ss-active-child").each(function(i,v){
			positions[$(this).index()] = $(this).data('text');
		});
		return positions;
	} 

	TextManager.prototype.setOnClick = function(obj){
		$(".entry-selected").each(function(i,v){
			if(!$(obj).is(this)){
				$(this).removeClass("entry-selected");
			}
		})
		$(obj).toggleClass("entry-selected");
	}

	TextManager.prototype.addTextPane = function(){
		var self = this;
		$("#add-text").appendTo("#add-text-pane");
		var val = this.saveText()
		var pane = this.createPane(val);
		$(".shift-text").trigger("ss-rearrange")
		$(".shift-text").shapeshift({
		    align: "left",
		    dragWhitelist: ".dragable",
		    enableCrossDrop:false
		});
		$("#add-text").removeClass('ss-active-child');
		$("#add-text-popup").removeClass('ss-active-child');
		pane.click(function(){
			self.setOnClick(this);
		})
		
		if(this.textCount >= this.textNumber){
			this.disableAddText();
		}
		this.sendToServer();
	} 

	TextManager.prototype.disableAddText = function(){
		$("#add-text").attr('href', "#add-text-popup-disabled")
	}

	TextManager.prototype.enableAddText = function(){
		$("#add-text").attr('href', "#add-text-popup")
	}

	TextManager.prototype.deleteText = function(entry){
		entry.remove()
		this.sendToServer();
		$(".shift-text").trigger("ss-rearrange")
		$("#add-text").removeClass('ss-active-child');
		this.textCount--;
		$("#add-text-number").html(this.textCount); 
	}

	var text = new TextManager();
	var project = new Project(text);
	
});