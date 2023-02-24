odoo.define('website_portal_design.user_image', function(require) {
    $(document).ready(function() {
        var ajax = require('web.ajax');
        var rpc = require('web.rpc');

        $('.image_loaded').change(update_user_image);         

        function update_user_image()
        {
            var image_input = null;
            var self = this;
            var image = document.querySelector('.image_loaded').files[0];
            if (image) {
            	var reader1 = new FileReader();
            	reader1.readAsDataURL(image);
            	reader1.onload = function(e){
            		image_input = e.target.result;
					ajax.rpc('/update-image',{'img_attachment':image_input}).then(function(data){
						if(data){
							$("#user_image_load").html(data)
						}
					});
            	}
            }
           
        }
    })
})