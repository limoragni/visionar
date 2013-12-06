$(document).ready(function() {
	
	/*var Socket = function(){
		this.socket = {};
		this.init();
	}

	Socket.prototype.init = function(){
	 	this.socket = new io.Socket(null, {port: _SOCKET, rememberTransport: false});
      	this.socket.connect();
    }*/

	var Project = function(){
		this.urlhash = $(location).attr('pathname').split('/')[2];
		this.init();
	}

	Project.prototype.init = function(){
		
		this.setUploader();
		var self = this;
		
		$("#render").click(function(){
			self.render();
		})

		$("#delete-media").click(function(){
			self.deleteMedia();
		});

		$(".hippster").shapeshift({
		    minColumns: 3,
		    align: "left",
		});

		$("#save-project").click(function(){
			self.save();
		})

		$(".change-media").each(function(i, v){
			$(v).click(function(){
				self.changeMedia($(this));
			})
		});  
		this.resetDragDrop();
		this.disableFileInputDrag();
		this.setSelectEvent();
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
		var entry = "<div data-mediatype='Imagen' class='entry'>" +
						"<input type='file' />" +
						"<h3 class='file-input-inside'><i class='icon-large icon-camera'></i>Agregar Imagen</h3>" +
					"</div>"

		$($(".hippster")[0]).append(entry);
	}
	
	Project.prototype.getPositions = function(){
		var positions = [];
		$(".ss-active-child").each(function(i,v){
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
		    align: "left"
		});
	}
	
	Project.prototype.setOnClick = function(obj){
		$(".entry-selected").each(function(i,v){
			if(!$(obj).is(this)){
				console.log(this)
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
	       		positions: JSON.stringify(self.getPositions()),
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
		       		$(".hippster").trigger("ss-rearrange");
		       		self.resetDragDrop();
		       		self.disableFileInputDrag();
		        },
		        error: self.logErrors,
		    }); 
		}
	}

	Project.prototype.createVideo = function(url){
		var self = this;
		$("#video").html("<video width='650' height='400' controls> <source src='"+url+"' type='video/ogg' </video>")
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
		       			self.createVideo(data.response);
		       			clearInterval(interval);
		       		}
		        },
		        error: self.logErrors,
		    }); 
	}

	Project.prototype.askPreview = function(){
		var self = this;
		var interval = setInterval(function(){
			self.getPreview(interval);
		}, 10000)
	}

	/*var socketio = new Socket();*/
	var project = new Project();
	/*socketio.socket.send('TEXT');*/
	
});