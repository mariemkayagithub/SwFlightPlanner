

global_onload=0;
/*Helper to support multiple onload functions easily*/ 
function addLoadEvent(func) { 
	var oldonload = global_onload; 
	if (typeof global_onload != 'function') { 
	    global_onload = func; 
	} else { 
	    global_onload = function() { 
	      if (oldonload) { 
	        oldonload(); 
	      } 
	      func(); 
	    } 
	}
}
	 
/*Belongs to base.mako but loaded here to reduce bw*/
function fixcontentsize()
{
	if (window.innerHeight>300)
	{
		var hh=document.getElementById('content').offsetTop;		
		document.getElementById('content').style.height=''+parseInt(window.innerHeight-2.1*hh)+'px';
	}
}
	 