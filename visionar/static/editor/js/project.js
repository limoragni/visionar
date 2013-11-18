$(document).ready(function() {
	
	var Project = function(){
		this.inputNumber = 1;
	}

	Project.prototype.init = function(){

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
			
			upl.init();
		},
		success: function(d, i){
			var p = project.inputNumber++; 
			$("#files").append(
				"<div class='entry'>" +
					"<input type='file' id='file-" + p + "' data-position = '"+ p +"'/>" +
					"<h3>+</h3>" +
					"</div>"

			);

			var div = $(i).parent();
			div.addClass("entry-filled");
			div.html('<img data-id="'+d.id+'" src="'+ d.thumb +'"/>');
			div.click(onTouch);
		
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
		        },
		        error: function(xhr, errmsg, err){
		    		console.log(errmsg);
		        	console.log(xhr);
		        	console.log(err);
		        }
		    }); 
		}
		 
	});
	
	$(".entry-filled").each(function(i,v){
		$(v).click(onTouch);
	})
});