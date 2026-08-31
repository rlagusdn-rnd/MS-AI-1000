cm = {pop_close_url:"",
    init: function () {

    },
    //region === FILE ===
    add_image: function (fileid) {
        $('#file_'+fileid).click();
    },
    after_select_image: function (fileid) {
        let file = $('#file_' + fileid).get(0).files[0];
        if (file == null) return;
        if (file.type.substring(0, 5) != "image") {
            cm.popmsg("이미지만 업로드 가능합니다.");
            return;
        }
        let formdata = new FormData();
        formdata.append("file", file);
        formdata.append("type", "blob");
        formdata.append("file", file);
        formdata.append("type", "blob");
        let ajax = new XMLHttpRequest();
        ajax.dataType = "json";
        ajax.addEventListener('load', function (e) {
            let data = JSON.parse(e.target.responseText);
            if (data.result == 0) {
                //cm.olog("image", data);
                if ($("#image_location").length > 0) $("#image_location").val(data.location);
                if ($("#image_name").length > 0) $("#image_name").val(data.name);
                if ($("#image_size").length > 0) $("#image_size").val(data.size);
                if ($("#image_type").length > 0) $("#image_type").val(data.type);
                if ($("#image_ext").length > 0) $("#image_ext").val(data.ext);
            } else alert(data.errmsg);
        }, false);
        ajax.addEventListener('error', function (e) {
            alert("프로필 파일 업로드 에러가 발생했습니다.");
        }, false);
        ajax.open("POST", "/Common/Upload/upload.html");
        ajax.send(formdata);
    },
    add_file: function () {
        $('#file').click();
    },
    after_select_file: function () {
        let file = $('#file').get(0).files[0];
        if (file == null) return;
        let formdata = new FormData();
        formdata.append("file", file);
        formdata.append("type", "blob");
        let ajax = new XMLHttpRequest();
        ajax.dataType = "json";
        ajax.addEventListener('load', function (e) {
            let data = JSON.parse(e.target.responseText);
            if (data.result == 0) {
                //cm.olog("image", data);
                if ($("#file_location").length > 0) $("#file_location").val(data.location);
                if ($("#file_name").length > 0) $("#file_name").val(data.name);
                if ($("#file_size").length > 0) $("#file_size").val(data.size);
                if ($("#file_type").length > 0) $("#file_type").val(data.type);
                if ($("#file_ext").length > 0) $("#file_ext").val(data.ext);
            } else alert(data.errmsg);
        }, false);
        ajax.addEventListener('error', function (e) {
            alert("프로필 파일 업로드 에러가 발생했습니다.");
        }, false);
        ajax.open("POST", "/Common/Upload/upload.html");
        ajax.send(formdata);
    },
    download: function (param) {
        $('[name=fdownload]').attr('src', '/Common/Upload/download.html?p=' + param);
    },
    //endregion

    //region === ACTION ===

    submit: function (form, callback=null) {
        if (form == undefined) {
            alert("잘못된 접근입니다.");
            return;
        }
        if (!cm.form_check(form)) return;
        let formData = new FormData(form);
        $.ajax({
            cache: false,
            url: form.action,
            processData: false,
            contentType: false,
            type: 'POST',
            data: formData,
            success: function (json) {
                cm.hide_mask();
                try {
                    if(json.error!= undefined && json.error != "") cm.popmsg(json.error);
                    else if (json.action != undefined && json.action != "") eval(json.action);
                    if(callback!=null && json.data != undefined && json.data != ''){
                        callback(json.data);
                    }
                } catch (ex) {
                    cm.log(json);
			        console.log(form.action);
                    alert("에러가 발생하였습니다. 관리자에게 문의하여 주세요.");
                }
            },
            error: function (xhr, status) {
                cm.hide_mask();
                cm.log(xhr.responseText);
                alert("에러가 발생하였습니다. 관리자에게 문의하여 주세요. : " + xhr.responseText);
            }
        });
    },
    form_check:function(f, obj){
        if(obj!=null) obj.disabled=true;
        let rtn_value = true;
        for (let i=0; i<f.elements.length; i++)
        {
            let e = f.elements[i];
            if ($(e).attr("chk") == undefined) continue;
            let value = e.value.trim();
            if (value.length == 0)
            {
                if ($(e).attr("msg") == undefined){cm.popmsg($(e).attr("name")+"을(를) 입력하세요!");}
                else{cm.popmsg($(e).attr("msg"));}
                e.focus();
                rtn_value = false;
                break;
            }

            if ($(e).attr("chk") == "str")
            {
                if (value.length == 0)
                {
                    if ($(e).attr("msg") == undefined){cm.popmsg($(e).attr("name")+"을(를) 입력하세요!");}
                    else{cm.popmsg($(e).attr("msg"));}

                    e.focus();
                    rtn_value = false;
                    break;
                }
                if ($(e).attr("min") != undefined)
                {
                    if (value.length < parseInt($(e).attr("min")))
                    {
                        if ( ($(e).attr("msg")) == "undefined"){cm.popmsg($(e).attr("name")+" 값은 "+($(e).attr("min"))+" 보다 같거나 커야 됩니다.");}
                        else{cm.popmsg($(e).attr("msg"));}

                        e.focus();
                        rtn_value = false;
                        break;
                    }
                }
                if ($(e).attr("max") != undefined)
                {
                    if (value.length > parseInt($(e).attr("max")))
                    {
                        if ( ($(e).attr("msg")) == "undefined"){cm.popmsg($(e).attr("name")+" 값은 "+($(e).attr("max"))+" 보다 같거나 커야 됩니다.");}
                        else{cm.popmsg($(e).attr("msg"));}

                        e.focus();
                        rtn_value = false;
                        break;
                    }
                }
            }

            if ($(e).attr("chk") == "int")
            {
                if (isNaN(value))
                {
                    cm.popmsg("숫자만 입력 가능합니다.");
                    e.focus();
                    rtn_value = false;
                    break;
                }

                value = parseInt(value);

                if ( ($(e).attr("min")) != undefined)
                {
                    if (value < parseInt($(e).attr("min")))
                    {
                        if ( ($(e).attr("msg")) == undefined){cm.popmsg($(e).attr("name")+" 값은 "+($(e).attr("min"))+" 보다 같거나 커야 됩니다.");}
                        else{cm.popmsg($(e).attr("msg"));}

                        e.focus();
                        rtn_value = false;
                        break;
                    }
                }

                if ( ($(e).attr("max")) != undefined)
                {
                    if (value > parseInt($(e).attr("max")))
                    {
                        if ( ($(e).attr("msg")) == undefined){cm.popmsg($(e).attr("name")+"은(는) "+($(e).attr("max"))+" 보다 같거나 작아야 됩니다.");}
                        else{cm.popmsg($(e).attr("msg"));}

                        e.focus();
                        rtn_value = false;
                        break;
                    }
                }
            }

            if ($(e).attr("chk") == "function")
            {
                //cm.popmsg('function');
                try{result = eval($(e).attr("func"));}
                catch(ex){cm.popmsg("입력값 검사 함수 " + $(e).attr("func") + " 에 오류가 있습니다.");}

                if (!result)
                {
                    if ( ($(e).attr("msg")) == undefined){cm.popmsg($(e).attr("name")+"에 입력한 값이 틀립니다.");}
                    else{cm.popmsg($(e).attr("msg"));}

                    e.focus();
                    rtn_value = false;
                    break;
                }
            }
        }
        if(obj!=null) obj.disabled=false;
        return rtn_value;
    },
    //endregion

    //region === LAYER POP ===
    popmsg_url: function (msg, reloadurl) {
        cm.popmsg(msg);
        cm.pop_close_url = reloadurl;
    },
    popmsg_refresh: function (msg) {
        cm.popmsg(msg);
        cm.pop_close_url = "0";
    },
    popmsg_confirm: function (msg, callback) {
        cm.pop_close_url = "";
        let popStr = "<div id='popWrap'><div id='popBg' onclick=\"cm.closepop();\"></div><div id='popContents' class='pop-box' >";
        popStr+="<div class=\"pop-title\">Confirm</div>";
        popStr+="<div class=\"pop-con\">"+(msg)+"</div>";
        popStr+="<div class=\"pop-btn-wrap\">";
        popStr+="<a id=\"btn_pop_confirm\" class=\"pop-btn green fl\" href=\"javascript:;\">확인</a>";
        popStr+="<a class=\"pop-btn\" href=\"javascript:;\" onclick=\"cm.closepop();\">닫기</a>";
        popStr+="</div>";
        popStr+="<a class=\"pop-close\" href=\"javascript:;\" onclick=\"cm.closepop();\"></a>";
        popStr+="</div></div>";
        $("html").append(popStr);
        $("#btn_pop_confirm").focus();
        document.getElementById("btn_pop_confirm").onclick = callback;
    },
    popmsg: function (msg) {
        cm.pop_close_url = "";
        let popStr = "<div id='popWrap'><div id='popBg' onclick=\"cm.closepop();\"></div><div id='popContents' class='pop-box' >";
        popStr+="<div class=\"pop-title\">Alert</div>";
        popStr+="<div class=\"pop-con\">"+(msg)+"</div>";
        popStr+="<div class=\"pop-btn-wrap\"><a class=\"pop-btn\" href=\"javascript:;\" onclick=\"cm.closepop();\">닫기</a></div>";
        popStr+="<a class=\"pop-close\" href=\"javascript:;\" onclick=\"cm.closepop();\"></a>";
        popStr+="</div></div>";
        $("html").append(popStr);
        $(".pop-btn").focus();
    },
    closepop: function () {
        $('#popWrap').remove();
        if (cm.pop_close_url == "0") location.reload();
        else if (cm.pop_close_url != "") location.href = cm.pop_close_url;
    },
    /* LAYER POP */
    show_pop: function (pop_id='layer_pop') {
        if($("#"+pop_id).length>0) $("#"+pop_id).show();
    },
    hide_pop: function () {
        if($(".layer_pop").length>0) $(".layer_pop").hide();

    },
    //endregion

    //region === ETC ===
    set_cookie:function(name,value) {
        var date = new Date();
        date.setTime(date.getTime() + (365*24*60*60*1000));
        document.cookie = name + "=" + (value || "")  + "; expires=" + date.toUTCString() + "; path=/";
    },
    get_cookie:function(name, default_value='') {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return default_value;
    },
    pad_left: function(value, length=2, char='0') {
        return String(value).padStart(length,char);
    },
    notlast: function(data) {
        data = String(data);
        if(data=="") return data;
        else return data.substring(0,data.length-1);;
    },
    cut_tag: function(html) {
        return html.replace(/<\/?[^>]+(>|$)/g, "");
    },
    floating_label: function(obj) {
        let parent=$(obj).parents('.inputList');
        parent.find('li.on').removeClass('on');
        $(obj).addClass('on');
    },
    encodekr:function(str) {
    return (encodeURIComponent(str));
},
    replace: function (data, s_old, s_new) {
        //return data.replaceAll(s_old, s_new);
        return data.split(s_old).join(s_new);
    },
    toast: function (msg) {
        //alert(msg); if(msg.indexOf("복습내역")>0) return;
        if(msg=="") return;
        $(".toast").remove();
        let el = document.createElement('div');
        el.className = "toast";
        el.innerHTML = msg;
        $("body").append(el);
        el.className = "toast show";
        setTimeout(function () {
            $(".toast").remove();
            //el.className = "toast";
        }, 2800);
    },
    show_mask: function (msg = '') {
        let message = (msg == '' ? 'PROCESSING ...' : msg);
        let el = $("<div class='backdrop-mask' onclick='cm.hide_mask()'><div class='mask-message ac'>" + message + "</div></div>");
        $("body").append(el);
        $(el).fadeIn(200);
    },
    hide_mask: function () {
        $('.backdrop-mask').last().remove();
    },
    timeunique: function () {
        return moment().format("YYYYMMDD_HHmmss_SSS");
    },
    unique: function () {
        return Math.random().toString(36).substr(2, 9);
    },
    hweekday: function (i) {
        let hweek=['일', '월','화','수','목','금','토'];
        return hweek[i];
    },
    log: function (msg) {
        console.log(msg);
    },
    //endregion

};
