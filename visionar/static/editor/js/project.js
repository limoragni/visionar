$(document).ready(function() {
	
	var Project = function(){
		
	}

	Project.prototype.init = function(){

	}

	Project.prototype.save = function(){

	}

	Project.prototype.render = function(){

	}

	Project.prototype.createVideo = function(){

	}

	Project.prototype.createFileInput = function(){
		
	}

	var Media = function(){

	}
	
	Media.prototype.upload = function(){

	}

	Media.prototype.ontouch = function(){
		
	} 

	var onTouch = function(){
		var self = this;
			$(".entry-selected").each(function(i,v){
				if(!$(self).is(this)){
					$(this).removeClass("entry-selected");
				}
			})
			$(this).toggleClass("entry-selected");
	}

	var disableDrag = function(){
		var p = $("input[type=file]").parent();
		console.log(p)
		p.removeClass('ss-active-child');
	}

	var project = new Project();
	var urlhash = $(location).attr('pathname').split('/')[2];
	
	var upl = new Uploader("/project/uploadImage/", {
		data:{
			project: urlhash,
		},
		
		onChange : function(i){
			console.log(i)
			
			$(i).css("display", "none")
			$(i).siblings().css("display", "none")
			$(i).parent().append("<h4>Loading...</h4>")
			
			var p = project.inputNumber++; 
			$($(".hippster")[0]).append(
				"<div class='entry'>" +
					"<input type='file' />" +
					"<h3>+</h3>" +
					"</div>"
			);
			disableDrag();
			upl.init();
		},
		success: function(d, i){
			var div = $(i).parent();
			div.addClass("entry-filled");
			div.data('id', d.id); 
			div.html('<img data-id="'+d.id+'" src="'+ d.thumb +'"/>');
			div.click(onTouch);
			$(".hippster").trigger("ss-rearrange")
			$(".hippster").shapeshift({
			    minColumns: 3,
			    align: "left",
			});
			disableDrag()
		},
		error: function(e){
			console.log(e);
		}
	})

	$("#render").click(function(){
		$("#video").html("Loading....");
		$.ajax({
	    	url: "/project/render/",
	       	type: 'POST',
	       	data: {
	       		project: urlhash,
	       		user: _USER,
	       		csrfmiddlewaretoken: _csrftoken

	       	},
	        success: function(data, status, xhr) {
	       		$("#video").html("<video width='650' height='400' controls> <source src='/media/renders/"+urlhash+"1-250.ogv' type='video/ogg' </video>")
	        },
	        error: function(xhr, errmsg, err){
	    		console.log(errmsg);
	        	console.log(xhr);
	        	console.log(err);
	        }
	    });     
	})

	$("#delete-media").click(function(){
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
		       		disableDrag();
		        },
		        error: function(xhr, errmsg, err){
		    		console.log(errmsg);
		        	console.log(xhr);
		        	console.log(err);
		        }
		    }); 
		}
		 
	});

	var getPositions = function(){
		var positions = [];
		$(".ss-active-child").each(function(i,v){
			positions[$(this).index()] = $(this).data('id');
		});
		return positions;
	}

	$("#save-project").click(function(){
		$.ajax({
	    	url: "/project/save/",
	       	type: 'POST',
	       	data: {
	       		project: urlhash,
	       		user: _USER,
	       		positions: JSON.stringify(getPositions()),
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
	})  	
	
	$(".entry-filled").each(function(i,v){
		$(v).click(onTouch);
	})
	
	$(".hippster").shapeshift({
	    minColumns: 3,
	    align: "left",
	});
	disableDrag()

	console.log(getPositions());


});