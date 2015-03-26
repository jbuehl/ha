    function redirect() {
    	   location='"+location+"';
    }
    window.setInterval('redirect()',"+str(interval*1000)+");

