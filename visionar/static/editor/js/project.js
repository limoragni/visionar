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
		
		$("#final-render-button").click(function(e){
			if(!self.validate()){
				e.preventDefault();
				
			}else{
				$("#final-render-title").html("Aguarde a ser redireccionado")
				window.location = "/project/checkout/"+ self.urlhash;
			}
		})

		$("#render").click(function(){
			if(self.validate()){
				$("#preview-title").html("Vista Previa")
				self.save(true);	
			}else{
				$("#preview-title").html("Por favor, cargue todos los textos e imagenes necesarios")
			}
		})

		$("#cancel_render").click(function(){
			self.cancelRender();
		});

		$("#delete-text").click(function(){
			var entry = $($(".entry-selected")[0]);
			if(entry.hasClass("entry-text")){
				self.text.deleteText(entry);
			}
		})

		$("#delete-media").click(function(){
			var entry = $($(".entry-selected")[0]);
			if(!entry.hasClass("entry-text")){
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
		element.parent().append("<img src='"+ _STATIC_PATH +"visionar/images/loader.gif'>")
		element.parent().removeAttr('data-mediatype')
	}

	Project.prototype.newFileField = function(){
		this.imageCount++;
		var entry = "<div data-mediatype='Imagen' class='entry'>" +
						"<h4><span id='image-number'>"+this.imageCount+ "</span>/" + this.imageNumber+"</h4>" +
						"<input type='file' />" +
						"<h3 class='file-input-inside'><i class='icon-large icon-camera'></i>Agregar Imagen</h3>" +
						"<span id='cover-add-image' ></span>" +
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
	
	Project.prototype.save = function(render){
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
	        	if(render){
	        		self.render();
	        	}
	        	if(!render && data.response){
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

	Project.prototype.validate = function(){
		if(this.text.textCount == this.text.textNumber && this.imageCount == this.imageNumber){
			return true;
		}else{
			return false;
		}
	}

	Project.prototype.render = function(){
		var self = this;
		$("#video").html("<img style='margin-bottom:10px;'src='"+ _STATIC_PATH +"visionar/images/loader.gif'>");
		$.ajax({
	    	url: "/project/render/",
	       	type: 'POST',
	       	data: {
	       		project: self.urlhash,
	       		user: _USER,
	       		csrfmiddlewaretoken: _csrftoken
			},
	        success: function(data, status, xhr) {
	       		if(data.error){
	       			//TODO: POPUP AVISANDO QUE EL SERVER ESTA CAIDO 
	       		}else{
	       			setTimeout(function(){
		       			self.askPreview();
		       		}, 1000)
	       		}
	        },
	        error: self.logErros,
	    }); 
	}

	Project.prototype.cancelRender = function(){
		var self = this;
		$.ajax({
	    	url: "/project/cancelRender/",
	       	type: 'POST',
	       	data: {
	       		project: self.urlhash,
	       		user: _USER,
	       		csrfmiddlewaretoken: _csrftoken
			},
	        success: function(data, status, xhr) {
	       		console.log(data);
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
		       		if(self.imageCount < self.imageNumber){
		       			self.enableAddImage();
		       		}
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
		$("#cover-add-image").css({
			width: 150,
			height: 150,
			zIndex: 99000,
			position:'absolute',
			top: 0,
			left:0
		})

		$("#cover-add-image").click(function(){
			$.magnificPopup.open({
		        items: {
		            src: '#add-image-popup-disabled' 
		        },
		        type: 'inline'
		    });
		})
	}

	Project.prototype.enableAddImage = function(){
		var p = $("input[type=file]").parent();
		$("input[type=file]").prop('disabled', false);
		$("#cover-add-image").css('z-index', 0)
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
		this.limit = 30;
		this.textValid = true;
		this.init();
	}

	TextManager.prototype.init = function(){
		var self = this;

		this.textCount = parseInt(_TEMPLATE_TEXT_COUNT);
		this.textNumber = parseInt(_TEMPLATE_TEXT_NUMBER);
		this.urlhash = $(location).attr('pathname').split('/')[2];

		$(".shift-text").shapeshift({
		    minColumns: 3,
		    enableCrossDrop: false,
		    dragWhitelist: ".dragable",
		    align: "left",
		});
		
		$("#add-text-button").click(function(e){
			if(self.textValid){
				self.addTextPane();
			}else{
				e.preventDefault();
			}
		})
		$("#add-text").removeClass('ss-active-child');
		$("#add-text-popup").removeClass('ss-active-child');

		$("#add-text").click(function(){
			$("#add-text-field").val("");
			$("#add-text-button").removeClass('popup-modal-dismiss')
			$("#add-text-button").css('color', '#666666')
			$("#text-length").html(self.limit)
			$("#text-length").css('color', '#444444')
			self.textValid = false;
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

		$("#add-text-field").keyup(function(event) {
			

			if($(this).val().length > self.limit){
				$(this).css('color', '#CC0077')
				$("#text-length").html(0)
				$("#text-length").css('color', '#CC0077')
				self.textValid = false;
				$("#add-text-button").removeClass('popup-modal-dismiss')
				$("#add-text-button").css('color', '#666666')
			
			}else{
				self.textValid = true
				$("#add-text-button").addClass('popup-modal-dismiss')
				$(this).css('color', '#EEEEEE')
				$("#text-length").html(self.limit - $(this).val().length)
				$("#text-length").css('color', '#444444')
				$("#add-text-button").css('color', '#3498db')

				if($(this).val().length == 0){
					$("#add-text-button").removeClass('popup-modal-dismiss')
					$("#add-text-button").css('color', '#666666')
					self.textValid = false;
				}
			}
			
		});
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
		if(this.textCount < this.textNumber){
			this.enableAddText();
		} 
	}

	var text = new TextManager();
	var project = new Project(text);
	
});