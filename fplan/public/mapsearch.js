searchopinprogress=0;
searchagain=0;
searchagainfor='';
searchpopup=0;
searchpopup_sel=0;
searchlastdata=[];

function findPos(obj) {
	var curleft = curtop = 0;

	if (obj.offsetParent) {
		do {
			curleft += obj.offsetLeft;
			curtop += obj.offsetTop;			
		} while (obj = obj.offsetParent);
	}
	
	return [curleft,curtop];
}
function remove_searchpopup()
{
	var s=document.getElementById('searchpopup');
	s.style.display='none';
	searchpopup=0;
}
function searchsel(delta)
{
	if (searchpopup_sel>=0)
		searchpopup.childNodes[searchpopup_sel].style.background='#ffffff';
	searchpopup_sel+=delta;
	if (searchpopup_sel<0)
		searchpopup_sel=0;
	if (searchpopup_sel>=searchpopup.childNodes.length)
		searchpopup_sel=searchpopup.childNodes.length-1;
	if (searchpopup_sel>=0)
		searchpopup.childNodes[searchpopup_sel].style.background='#ff0000';
}

function on_search_keydown(event)
{

	if (searchpopup)
	{	
		//38=up, 40=ner, 13 = enter
		if (event.which==38)
		{ //up			
			searchsel(-1);
			return false;
		}
		if (event.which==40)
		{ //down
			searchsel(1);
			return false;
		}
		if (event.which==13)
		{			
			if (searchpopup_sel>=0 && searchpopup_sel<searchlastdata.length)
			{
				var d=searchlastdata[searchpopup_sel];
				add_waypoint(d[0],d[1]);
			}
			remove_searchpopup();
			return false;
		}
	}
	return true;
}
function on_search_keyup(keyevent)
{
	if (keyevent.which==38 || keyevent.which==40 || keyevent.which==13)
		return false;
	var s=document.getElementById('searchpopup');
	var field=document.getElementById('searchfield');
	if (searchopinprogress==1)
	{
		searchagain=1;
		searchagainfor=searchfor;		
		return;
	}
	function search_cb(req)
	{	
		searchopinprogress=0;
		
		if (req.responseText=='')
		{			
			s.style.display='none';
			searchpopup=0;
		}
		else
		{
			s.style.display='block';
			searchpopup=s;
			searchpopup_sel=-1;
			var pos=findPos(field);
			s.style.left=''+pos[0]+'px';
			s.style.top=''+(pos[1]+field.offsetHeight)+'px';
			searchlastdata=evalJSONRequest(req);
			
			var inner='';
			for(var i=0;i<searchlastdata.length;++i)
			{
				inner+='<p>'+searchlastdata[i][0]+'</p';
			}
			s.innerHTML=inner;
		}
	
		if (searchagain)
		{
			searchagain=0;
			search_destination(searchagainfor);				
		}
	}
	
	
	var params={};	
	params['search']=field.value;
	var def=doSimpleXMLHttpRequest(searchairporturl,
		params);
	def.addCallback(search_cb);	
}
/*
*/