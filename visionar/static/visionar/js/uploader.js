var Uploader = function(url, options){
	this.files = [];
	this.url = url;
	this.data = options.data;
	this.input = {};
	this.options = options;
	this.init();

}

Uploader.prototype.init = function(){
	var self = this;
	$("input[type=file]").change(function(event) {
		var inp = this;
		self.file = event.target.files[0];
		self.input = this;
		var reader = new FileReader();
		reader.onload = function(event){
			self.addFileData(event);
			self.options.onChange(inp);
			self.send();
		}
		reader.readAsDataURL(self.file);
	})
}

Uploader.prototype.send = function(){
	this.data['csrfmiddlewaretoken'] = _csrftoken
	this.addDynamicData();
	var self = this;
	$.ajax({
    	url: self.url,
       	type: 'post',
       	data: self.data,
        success: function(data, status, xhr) {
       		self.options.success(data, self.input);
       		//console.log(data);
        },
        error: function(xhr, errmsg, err){
    		self.options.error(errmsg);
    		console.log(errmsg);
        	console.log(xhr);
        	console.log(err);
        }
    });     
	
	
}

Uploader.prototype.addDynamicData = function(){
	var input = $(this.input)
	if(input.data()){
		for(var i in input.data()){
			this.data[i] = input.data(i);
		}
	}
	
}

Uploader.prototype.addFileData = function(e){
	this.data["filename"] = this.file.name;
    this.data["data"] = e.target.result;
}
