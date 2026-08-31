lg={
    init:function(){

    },
    login:function(){
        let f = flogin;
        if(!cm.form_check(f)) return;
        bw.send_cmd('login', {userid:f.userid.value.trim(), password:f.password.value.trim()}, function(){
            location.href = "manage.html";
        });
    },
    exit:function(){
        cm.popmsg_confirm("프로그램을 종료하시겠습니까?", function () {
            bw.send_cmd('mg-exit', null, function(){

            });
        });
    },
}
mg={
    nav:"", userid:"", is_admin:0,
    info:{is_admin:1, userid:"dev.msvision",
            cameras:[
                {property:{name:"카메라 1", no:"Camera 1", ip:"117.17.159.31", stream_no:"Stream 2", port:80, mac:"mac1", userid:"admin", password:"admin"},
                    roi:[{event_kind:"침입", pnts:[{x:0,y:0}]}], group_no:0, is_connected:1, image:{src:"", w:0,h:0, fps:0, datatime:""}
                    }],
            groups:[{name:"GROUP1", is_processing:0, is_recording:0, process_time:[{weekday:[], start:"18:00", end:"09:00"}], grid:2, page:0}],
            server:{name:"NVR", ip:"117.17.159.31", port:8081, userid:"", password:""},
            setting:{reconnect:{is_use:0, second:60}, folder:{record:"", snapshot:""}, userid:"", password:""},
            admin:{license_cnt:10, license_kind:[], logo:"", program_name:"", manual:""}
        },
    now_camera_no:-1, now_group_event_image:null,now_group_event_is_roi_edit:0, now_preview_page_no:0, now_group_no:-1, now_search_page_no:0,now_roi_no:-1,
    temp_roi:[],
    event_kinds:[{name:"침입", desc:"특정 영역에 객체가 진입 즉시 알람 발생 "}, {name:"배회", desc:"특정 영역에 객체가 배회할시 즉시 알람 발생 "},{name:"출입확인", desc:"특정 영역에 출입 발생시 즉시 알람 발생 "},{name:"방화", desc:"특정 영역에 방화 발생시 즉시 알람 발생 "},{name:"쓰러짐", desc:"특정 영역에 쓰러짐 발생시 즉시 알람 발생 "},{name:"투기", desc:"특정 영역에 투기 발생시 즉시 알람 발생 "},{name:"싸움", desc:"특정 영역에 싸움 발생시 알람 발생 "}],
        undo_camera:null, temp:null,
    init:function(){
        const canvas = document.getElementById("group_event_canvas");
        canvas.addEventListener('contextmenu', function(e){
            e.preventDefault();
            e.stopPropagation();
            mg.group_event_redraw_roi(e);

        });
        $('#group_time_start, #group_time_end').timepicker({
            timeFormat: 'HH:mm',
            interval: 30,
            dynamic: false,
            dropdown: true,
            scrollbar: true,
            zindex:100
        });
        bw.send_cmd('mg-init',null, function (data) {
            //cm.show_pop();
            let option="", html="", no, in_html='', out_html="";
            //region TOP & LEFT
            mg.userid = data.userid;
            mg.is_admin = data.is_admin;
            mg.info = data.info;
            $("#userid").text(data.userid);
            $("#btn_userid").text(data.userid);
            $("#pop_userid").text(data.userid);
            if(!mg.is_admin) {
                $("#li_tab_menu_manager").remove();
            }
            $("#logo").attr("src", "./images/logo.png");
            bw.send_cmd('mg-load-image',mg.info.admin.logo, function (data)
            {
                $("#logo").attr("src", data);
            });
            $("#program_name").attr("src", mg.info.admin.program_name);
            for(let i=1;i<=mg.info.admin.license_cnt;i++) option += '<option valu="Camera '+i+'">Camera '+i+'</option>';
            $("#sel_camera_no").html(option);

            $("#logo").attr("src", mg.info.admin.logo);
            $("#program_name").attr("src", mg.info.admin.program_name);
            //endregion

            //region RIGHT PREVIEW
            html="";
            for(let i=0;i<4;i++) {
                html += '<tr>';
                for(let j=0;j<4;j++) {
                    no = i*4+j;
                    html += '<td><div id="preview_cam_'+no+'" class="group-camera" ><div class="title">카메라 '+(no+1)+'</div></div></td>';
                }
                html += '</tr>';
            }
            $("#preview_tbody").html(html);
            //endregion

            //region RIGHT SERVER
            $("#td_svr_name").html(mg.info.server.name);
            $("#td_svr_ip").html(mg.info.server.ip);
            fsvr.name.value = mg.info.server.name;
            fsvr.ip.value = mg.info.server.ip;
            fsvr.port.value = mg.info.server.port;
            fsvr.userid.value = mg.info.server.userid;
            fsvr.password.value = mg.info.server.password;

            //endregion

            //region RIGHT SETTING
            $('#set_stime, #set_etime').timepicker({
                timeFormat: 'HH:mm:ss',
                interval: 30,
                dynamic: false,
                dropdown: true,
                scrollbar: true,
                zindex:100
            });
            $("#set_sdate, #set_edate").datepicker();
            $("#set_sdate, #set_edate").val(moment().format("YYYY-MM-DD"));
            option="";
            mg.event_kinds.forEach(function (event_kind, i) {
                option += '<option value="'+event_kind.name+'">'+event_kind.name+'</option>';
            });
            $("#event_kind").html(option);
            $("#event_kind").val(mg.event_kinds[0].name);

            fset_reconnect.is_use.checked = mg.info.setting.reconnect.is_use;
            fset_reconnect.second.value =  mg.info.setting.reconnect.second;
            fset_folder.record.value = mg.info.setting.folder.record;
            fset_folder.snapshot.value = mg.info.setting.folder.snapshot;
            fset_privacy.userid.value = mg.info.setting.userid;
            mg.setting_select('search');
            //endregion

            //region RIGHT ADMIN
            mg.event_kinds.forEach(function (event_kind, i) {
                if(mg.info.admin.license_kind.includes(event_kind.name)) in_html += mg._get_admin_kind_html_templet(i, event_kind.name);
                else {
                    out_html += mg._get_admin_kind_html_templet(i, event_kind.name);
                }
            });
            $("#admin_kind_out").html(out_html);
            $("#admin_kind_in").html(in_html);
            fadmin.license_cnt.value = mg.info.admin.license_cnt;
            fadmin.logo.value = mg.info.admin.logo;
            fadmin.program_name.value = mg.info.admin.program_name;
            fadmin.manual.value = mg.info.admin.manual;
            mg.admin_select('license');
            //endregion

            mg.camera_renew_list();
            mg.camera_select(0);
            //mg.select_nav("manager");
            //mg.select_nav("setting");
            //mg.select_nav("camera");
            mg.select_nav("group");
        });
    },

    select_nav:function (nav) {
        mg.nav = nav;
        $(".info-nav-tab-menu.on").removeClass('on');
        $("#tab_menu_"+nav).addClass('on');
        $(".tab-content.on").removeClass('on');
        $("#tab_"+nav).addClass('on');
        if(mg.nav=="camera"){
            mg.preview_renew();
        }
        else if(mg.nav=="group"){
            mg.group_renew();
        }
    },

    //region == LEFT CAMERA
    camera_renew_list:function () {
        let html="";
        mg.info.cameras.forEach(function(camera, i){
            html +='<tr id="ctr_'+i+'" onclick="mg.camera_select('+i+')">';
            html +='<td><div class="camera '+(camera.is_connected ? "on":"")+'"></div></td>';
            html +='<td>'+(camera.group_no==-1?"" : "G"+(camera.group_no+1))+'</td>';
            html +='<td>'+camera.property.name+'</td>';
            html +='<td>'+camera.property.no+'</td>';
            html +='<td>'+camera.property.ip+'</td>';
            html +='</tr>';
        });
        $("#ctbody").html(html);
        mg.preview_renew();
        if(mg.now_group_no>-1) mg.group_renew(mg.now_group_no);
    },
    camera_select:function (no) {
        mg.now_camera_no = no;
        $("#ctbody tr.on").removeClass('on');
        $("#ctr_"+no).addClass('on');
        let f = fcamera;
        if(mg.undo_camera==null) $("#btn_camera_undo").hide();
        else $("#btn_camera_undo").show();
        if(no==-1){
            f.name.value = "";
            f.no.value ="Camera 1";
            f.ip.value = "";
            f.stream_no.value = "Stream 2";
            f.port.value = "554";
            f.mac.value = "";
            f.userid.value = "";
            f.password.value = "";
            $("#btn_camera_remove").hide();
            $("#btn_camera_save").hide();
        }
        else {
            let property = mg.info.cameras[no].property;
            f.name.value = property.name;
            f.no.value = property.no;
            f.ip.value = property.ip;
            f.stream_no.value = property.stream_no;
            f.port.value = property.port;
            f.mac.value = property.mac;
            f.userid.value = property.userid;
            f.password.value = property.password;
            $("#btn_camera_remove").show();
            $("#btn_camera_save").show();
        }
    },
    camera_save:function (mode) {
        let f = fcamera;
        mg.temp=mg._get_camera_templet(f);
        if(mode==11) {
            if(!cm.form_check(f)) return;
            for(let i=0;i<mg.info.cameras.length;i++) {
                if(f.ip.value == mg.info.cameras[i].property.ip || f.no.value == mg.info.cameras[i].property.no){
                    cm.popmsg("동일한 no 또는 IP의 카메라가 있습니다.");
                    return;
                }
            }
            mg.undo_camera = null;
            bw.send_cmd('mg-camera-add', {no:-1, camera:mg.temp}, function(data){
                mg.info.cameras.push(data || mg.temp); //for browser test
                mg.camera_renew_list();
                mg.camera_select(mg.info.cameras.length-1);
                cm.toast('CAMERA ADDED');
            });
        }
        else if(mode == 12){
            if(!cm.form_check(f)) return;
            for(let i=0;i<mg.info.cameras.length;i++) {
                if(i!=mg.now_camera_no && (f.ip.value == mg.info.cameras[i].property.ip || f.no.value == mg.info.cameras[i].property.no)){
                    cm.popmsg("동일한 no 또는 IP의 카메라가 있습니다.");
                    return;
                }
            }
            mg.undo_camera =  ut.clone(mg.info.cameras[mg.now_camera_no]);
            mg.temp = ut.clone(mg.info.cameras[mg.now_camera_no]);
            mg.temp.property = {name:f.name.value, no:f.no.value, ip:f.ip.value, stream_no:f.stream_no.value, port:f.port.value, mac:f.mac.value, userid:f.userid.value, password:f.password.value};
            bw.send_cmd('mg-camera-update', {no:mg.now_camera_no, camera:mg.temp}, function(data){
                mg.info.cameras[mg.now_camera_no] = data || mg.temp; //for browser test
                mg.camera_renew_list();
                mg.camera_select(mg.now_camera_no);
                cm.toast('CAMERA SAVED');
            });

        }
        else if(mode == 13){
            if(mg.now_camera_no==-1) return;
            cm.popmsg_confirm("선택한 카메라를 삭제하시겠습니까?", function () {
                mg.undo_camera = null;
                bw.send_cmd('mg-camera-remove', {no:mg.now_camera_no, camera:null}, function(){
                    mg.info.cameras.splice(mg.now_camera_no, 1);
                    mg.camera_renew_list();
                    mg.camera_select(-1);
                    cm.closepop();
                    cm.toast('CAMERA DELETED');
                });
            });
        }
        else if(mode == 14){
            mg.temp = ut.clone(mg.undo_camera);
            mg.undo_camera = null;
            bw.send_cmd('mg-camera-update', {no:mg.now_camera_no, camera:mg.temp}, function(data){
                mg.info.cameras[mg.now_camera_no] = data || mg.temp; //for browser test
                mg.camera_renew_list();
                mg.camera_select(mg.now_camera_no);
                cm.toast('CAMERA UNDO');
            });
        }
    },
    _get_camera_templet:function (f) {
        let camera = {property:{name:"", no:"", ip:"", stream_no:"", port:80, mac:"", userid:"", password:""}, roi:[], group_no:-1, is_connected:0, image:{src:"", w:0,h:0, fps:0, datatime:""}};
        camera.property = {name:f.name.value, no:f.no.value, ip:f.ip.value, stream_no:f.stream_no.value, port:f.port.value, mac:f.mac.value, userid:f.userid.value, password:f.password.value};
        return camera;
    },
    camera_refresh:function () {
        bw.send_cmd('mg-camera-refresh', {}, function(data){
            mg.info.cameras = data;
            mg.camera_renew_list();
        });
    },
    //endregion

    //region == RIGHT CAMERA PREVIEW
    preview_renew:function () {
        if(mg.nav != 'camera') return;
        let total = Math.floor(mg.info.admin.license_cnt/16);
        if(mg.info.admin.license_cnt%16==0) total --;

        if(mg.now_preview_page_no>total || mg.now_preview_page_no<0) mg.now_preview_page_no=0;
        if(mg.now_preview_page_no==0) $("#btn_preview_prev").addClass("off");
        else $("#btn_preview_prev").removeClass("off");
        if(mg.now_preview_page_no==total) $("#btn_preview_next").addClass("off");
        else $("#btn_preview_next").removeClass("off");
        let no = mg.now_preview_page_no*16;
        for(let i=0;i<16;i++) {
            if(no<mg.info.cameras.length && mg.info.cameras[no].is_connected && mg.info.cameras[no].image.src != "" ){
                $("#preview_cam_"+i).css("background-image", "url("+mg.info.cameras[no].image.src+")");
                $("#preview_cam_"+i + " .title").text(mg.info.cameras[no].property.name);
            }
            else {
                $("#preview_cam_"+i + " .title").text("");
                $("#preview_cam_"+i).css("background-image", "none");
            }
            no ++;
        }
    },
    preview_next:function (direction) {
        mg.now_preview_page_no += direction;
        mg.preview_renew();
    },
    //endregion

    //region == RIGHT GROUP
    group_renew:function (no=-1) {
        if(mg.nav != 'group') return;
        let html="";
        mg.info.groups.forEach(function(group, i){
            html +=' <li><a id="grp_'+i+'" class="group-nav-tab-menu" href="javascript:;" onclick="mg.group_select('+i+')">'+group.name+'</a></li>';
        });
        html +=' <li><a class="group-nav-tab-menu add" href="javascript:;" onclick="mg.group_pop_edit(1)"><img src="./images/ico_add.svg" alt=""></a></li>';
        $("#group_nav_tab").html(html);
        if(mg.info.groups.length>0 && no==-1) no=0;
        mg.group_select(no);
    },
    group_select:function (no) {
        mg.now_group_no = no;
        $(".tab-content.group .group-nav-tab-menu.on").removeClass('on');
        $("#grp_"+no).addClass('on');
        if(no>-1) mg.group_grid_select(mg.info.groups[no].grid);
        else mg.group_next(0);
    },
    group_grid_select:function (grid) {
        if(mg.now_group_no==-1) return;
        let group = mg.info.groups[mg.now_group_no];
        mg.temp = grid;
        bw.send_cmd('mg-group-change-grid', {no:mg.now_group_no, grid:grid},function(){
            let grid = mg.temp;
            group.grid = mg.temp;
            group.page_no = 0;
            $(".btn-group-grid.on").removeClass('on');
            $("#btn_grid_"+grid).addClass('on');
            $("#table_group_camera_view").attr("class", "table group-camera-view grid"  + grid +"x"+grid);
            mg.group_next(0);
        });
    },
    group_next:function (direction) {
        if(mg.info.groups.length==0) {
            $(".group-control, .group-contents").hide();
        }
        else {
            if(mg.now_group_no==-1) return;
            $(".group-control, .group-contents").show();
            let group = mg.info.groups[mg.now_group_no];
            if(!group.is_processing) {
                $("#btn_group_analyze").attr("class", "btn btn-tiny btn-green-gradient").text("해석 시작");
                $("#group_analysis_desc").hide();
            }
            else {
                $("#btn_group_analyze").attr("class", "btn btn-tiny btn-red").text("해석 중지");
                $("#group_analysis_desc").show();
            }
            if(group.is_recording) $("#group_menu_record").addClass("on").text("녹화중");
            else $("#group_menu_record").removeClass("on").text("녹화 시작");
            group.page_no += direction;
            let cameras=[];
            mg.info.cameras.forEach(function(camera){
                if(camera.group_no==mg.now_group_no && camera.is_connected) cameras.push(camera);
            })
            let total = Math.floor(cameras.length / group.grid / group.grid);
            if(cameras.length%(group.grid * group.grid)==0) total --;
            if (group.page_no > total || group.page_no < 0) group.page_no = 0;

            if (group.page_no == 0) $("#btn_group_prev").addClass("off");
            else $("#btn_group_prev").removeClass("off");

            if (group.page_no == total) $("#btn_group_next").addClass("off");
            else $("#btn_group_next").removeClass("off");
            let no = group.page_no * group.grid * group.grid;
            let html="", image="", cname="", desc="";
            for (let i = 0; i < group.grid * group.grid; i++) {
                if(i==0) html += "<tr>";
                else if(i%group.grid==0) html += "</tr><tr>";
                if (no < cameras.length) {
                    image = "url(" + cameras[no].image.src + ")";
                    cname = cameras[no].property.name;
                    if(desc == "" ) desc = "FPS "+ cameras[no].image.fps+" | "+ cameras[no].image.datatime;
                }
                else {
                    image = "none";
                    cname = "";
                }
                html += '<td><div id="group_cam_" class="group-camera" style="background-image:'+image+'"><div class="title">'+cname+'</div></div></td>';
                no++;
            }
            html += "</tr>";
            $("#table_group_camera_view").html(html);
            $("#group_camera_desc").html(desc==""? "NO DATA" : desc);
        }
    },
    group_pop_edit:function (is_insert=0) {
        if(!is_insert && mg.now_group_no==-1) return;
        let in_html='', out_html='', text='';
        let f = fgroup_edit;
        if(is_insert){
            f.name.value="GROUP " + (mg.info.groups.length+1);
            mg.info.cameras.forEach(function (camera, i) {
                if(camera.group_no==-1) text="";
                else text="disabled";
                out_html += mg._get_group_camera_html_templet(i, text, camera.property.name);
            })
            $("#btn_group_delete").hide();
            $("#btn_group_add").show();
            $("#btn_group_save").hide();
        }
        else {
            f.name.value= mg.info.groups[mg.now_group_no].name;
            mg.info.cameras.forEach(function (camera, i) {
                if(camera.group_no==mg.now_group_no) in_html += mg._get_group_camera_html_templet(i, "", camera.property.name);
                else {
                    if (camera.group_no == -1) text = "";
                    else text = "disabled";
                    out_html += mg._get_group_camera_html_templet(i, text, camera.property.name);
                }
            })
            $("#btn_group_delete").show();
            $("#btn_group_add").hide();
            $("#btn_group_save").show();
        }
        $("#group_camera_out").html(out_html);
        $("#group_camera_in").html(in_html);
        cm.show_pop('pop_group_edit');
    },
    _get_group_camera_html_templet:function (i, text, name) {
        return '<div><input type="checkbox" name="grp_edit_camera_'+i+'" id="grp_edit_camera_'+i+'" '+text+'><label class="checkbox" for="grp_edit_camera_'+i+'">'+name+'</label></div>';
    },
    _get_admin_kind_html_templet:function (i, name) {
        return '<div><input type="checkbox" name="admin_kind_'+i+'" id="admin_kind_'+i+'" ><label class="checkbox" for="admin_kind_'+i+'">'+name+'</label></div>';
    },
    group_click_edit_move:function (direction) {
        if(direction==-1){//to out
            if($("#group_camera_in input[type=checkbox]:checked").length==0){
                cm.popmsg("먼저 이동할 카메라를 선택해야 합니다.");
                return;
            }
            $("#group_camera_in input[type=checkbox]:checked").each(function(i, input){
                $(input).parent().appendTo("#group_camera_out");
            });
        }
        else {
            if($("#group_camera_out input[type=checkbox]:checked").length==0){
                cm.popmsg("먼저 이동할 카메라를 선택해야 합니다.");
                return;
            }
            $("#group_camera_out input[type=checkbox]:checked").each(function(i, input){
                $(input).parent().appendTo("#group_camera_in");
            });
        }
    },
    group_save:function (mode) {
        let f, arr;
        if(mode==14) f = fgroup_event;
        else f = fgroup_edit;
        let camera, group, group_no;
        if(mode == 11){
            group = mg._get_group_templet();
            group_no = mg.info.groups.length;
        }
        else {
            group = ut.clone(mg.info.groups[mg.now_group_no]);
            group_no = mg.now_group_no;
        }
        if(mode==11) {
            if(!cm.form_check(f)) return;
            group.name = f.name.value;
            mg.temp = group;
            arr=[];
            mg.info.cameras.forEach(function(camera, i){
                if(camera.group_no == -1){
                    if($("#group_camera_in #grp_edit_camera_"+i).length > 0){
                        arr.push({no:i, group_no:group_no});
                    }
                }
            });
            bw.send_cmd('mg-group-add', {no:-1, group:mg.temp, camera_groups:arr},function(){
                arr.forEach(function(item, i){
                    mg.info.cameras[item.no].group_no = item.group_no;
                });
                mg.info.groups.push(mg.temp);
                mg.camera_renew_list();
                mg.camera_select(mg.now_camera_no);
                mg.group_renew(mg.info.groups.length-1);
                cm.hide_pop();
                cm.toast('GROUP ADDED');
            });
        }
        else if(mode == 12){
            if(mg.now_group_no==-1) return;
            if(!cm.form_check(f)) return;
            group.name = f.name.value;
            mg.temp = group;
            arr=[];
            mg.info.cameras.forEach(function(camera, i){
                if(camera.group_no == -1){
                    if($("#group_camera_in #grp_edit_camera_"+i).length>0){
                        arr.push({no:i, group_no:group_no})
                    }
                }
                if(camera.group_no == group_no){
                    if($("#group_camera_in #grp_edit_camera_"+i).length==0){
                        arr.push({no:i, group_no:-1})
                    }
                }
            });
            bw.send_cmd('mg-group-update', {no:mg.now_group_no, group:mg.temp, camera_groups:arr},function(){
                arr.forEach(function(item, i){
                    mg.info.cameras[item.no].group_no = item.group_no;
                });
                mg.info.groups[mg.now_group_no]= mg.temp;
                mg.camera_renew_list();
                mg.camera_select(mg.now_camera_no);
                mg.group_renew(mg.now_group_no)
                cm.hide_pop();
                cm.toast('GROUP SAVED');
            });
        }
        else if(mode == 13){
            if(mg.now_group_no==-1) return;
            cm.popmsg_confirm("선택한 그룹을 삭제하시겠습니까?", function () {
                arr=[];
                mg.info.cameras.forEach(function(camera, i){
                    if(camera.group_no == group_no){
                        arr.push({no:i, group_no:-1});
                    }
                });
                bw.send_cmd('mg-group-remove', {no:mg.now_group_no, group:mg.temp, camera_groups:arr}, function(){
                    arr.forEach(function(item, i){
                        mg.info.cameras[item.no].group_no = item.group_no;
                    });
                    mg.info.groups.splice(mg.now_group_no, 1);
                    mg.now_group_no = mg.info.groups.length-1;
                    mg.camera_renew_list();
                    mg.camera_select(mg.now_camera_no);
                    mg.group_renew(mg.now_group_no)
                    cm.hide_pop();
                    cm.closepop();
                    cm.toast('GROUP DELETED');
                });
            });
        }
        else if(mode == 14){
            if(mg.temp_roi.length ==0 || mg.temp_roi[mg.temp_roi.length-1].pnts.length< 2) {
                cm.popmsg("ROI를 설정해야 합니다.");
                return;
            }
            if(mg.now_group_event_is_roi_edit) mg.group_click_event_roi();
            camera = ut.clone(mg.info.cameras[f.sel_group_event_camera.value]);
            camera.roi = mg.temp_roi;
            mg.temp = camera;
            bw.send_cmd('mg-group-event-update', {no:f.sel_group_event_camera.value, camera:mg.temp},function(){
                mg.info.cameras[f.sel_group_event_camera.value] = mg.temp;
                cm.toast('GROUP EVENT SAVED');
            });
        }
        else if(mode == 15){
            //mg.temp = group; 이미 설정함
            bw.send_cmd('mg-group-time-update', {no:mg.now_group_no, group:mg.temp},function(){
                mg.info.groups[mg.now_group_no]= mg.temp;
                cm.hide_pop();
                cm.toast('GROUP SCHEDULE SAVED');
            });
        }
    },
    _get_group_templet:function () {
        let group = {name:"", is_processing:0, is_recording:0, process_time:[], grid:4, page:0};
        return group;
    },

    group_pop_event:function () {
        if(mg.now_group_no==-1) return;
        mg.now_group_event_is_roi_edit = 0;
        let options='';
        mg.info.cameras.forEach(function(camera,  i){
            if(camera.group_no==mg.now_group_no) {
                options += '<option value='+i+'>'+camera.property.name+'</option>'
            }
        })
        if(options==""){
            cm.popmsg("현재 그룹에는 카메라가 없습니다. 먼저 카메라를 추가하세요.");
            return;
        }
        $("#sel_group_event_camera").html(options);
        $("#sel_group_event_camera option:eq(0)").attr("selected", "selected");

        options='';
        mg.event_kinds.forEach(function(event_kind,  i){
            options += '<option value="'+event_kind.name+'">'+event_kind.name+'</option>'
        })
        $("#sel_group_event_kind").html(options);

        cm.show_pop('pop_group_event');
        mg.group_event_onchange_camera();
    },
    group_event_onchange_camera:function () {
        let value = $("#sel_group_event_camera").val();
        let camera = mg.info.cameras[parseInt(value)];
        //기존 단일 로이 확인해서 RESET
        if(camera.roi.length>0 && camera.roi[0].event_kind==undefined) camera.roi=[];
        mg.now_roi_no=(camera.roi.length==0 ? -1 : 0);
        mg.temp_roi = ut.clone(camera.roi);
        mg.group_event_onchange_kind();
        mg.now_group_event_image = null;
        let img = new Image();
        img.onload = function () {
            mg.now_group_event_image = this;
            mg.group_event_roi_wrap_renew();
        }
        img.src = camera.image.src;
    },
    group_event_roi_wrap_renew:function () {
        let html = "";
        mg.temp_roi.forEach(function(roi,  i){
            html += '<a id="btn_group_roi_'+i+'" onclick="mg.group_click_select_roi('+i+')" href="javascript:;" class="btn btn-micro">'+roi.event_kind+'</a>'
        });
        $("#group_roi_wrap").html(html);
        mg.group_click_select_roi(mg.now_roi_no);
    },
    group_event_redraw_roi:function (e=null) {
        if(e != null && !mg.now_group_event_is_roi_edit) return;
        const canvas = document.getElementById("group_event_canvas");
        const ctx = canvas.getContext("2d");
        let w=canvas.width, h=canvas.height;
        let x, y, is_right=0, is_double=0;
        let roi = mg.temp_roi;
        if (e) {
            e = e || window.event;
            if ("which" in e)  // Gecko (Firefox), WebKit (Safari/Chrome) & Opera
                is_right = (e.which == 3 ? 1:0);
            else if ("button" in e)  // IE, Opera
                is_right = (e.button == 2 ? 1:0);
            if(!is_right) {
                is_double = (e.detail == 2? 1:0);
            }
            if(is_right) {//back
                roi[mg.now_roi_no].pnts.pop();
            }
            else if(is_double) {//end
                mg.group_click_event_roi();
            } else {
                const {clientX, clientY, currentTarget} = e;
                const {left, top} = currentTarget.getBoundingClientRect();
                x = clientX - left;
                y = clientY - top;
                roi[mg.now_roi_no].pnts.push({x:x/w, y:y/h});
            }
        }
        // Clear the canvas
        ctx.clearRect(0, 0, w, h);
        ctx.globalAlpha  = 1;
        ctx.drawImage(mg.now_group_event_image, 0, 0, w, h);
        roi.forEach(function(eroi, i_roi) {
            // Iterate all the polygons
            let points = [];
            eroi.pnts.forEach(function (pos, i) {
                points.push({x: Math.round(pos.x * w), y: Math.round(pos.y * h)});
            });

            ctx.beginPath();
            points.forEach(function (pos, i) {
                if (i == 0) ctx.moveTo(pos.x, pos.y);
                else ctx.lineTo(pos.x, pos.y);
            });
            ctx.closePath();
            ctx.globalAlpha = 0.5;
            if(i_roi==mg.now_roi_no) ctx.fillStyle = '#13c10d';
            else ctx.fillStyle = '#777777';
            ctx.fill();

            ctx.globalAlpha = 1;
            if(i_roi==mg.now_roi_no) ctx.strokeStyle = '#13c10d';
            else ctx.strokeStyle = '#777777';
            ctx.lineWidth = 2;
            if (points.length > 0) ctx.lineTo(points[0].x, points[0].y);
            ctx.stroke();

            if (true) {
                if(i_roi==mg.now_roi_no) ctx.fillStyle = '#13c10d';
                else ctx.fillStyle = '#777777';
                ctx.globalAlpha = 1;
                points.forEach(function (pos, i) {
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 5, 0, 2 * Math.PI);
                    ctx.closePath();
                    ctx.fill();
                });
            }
        });
    },
    group_click_event_roi:function () {
        if(mg.now_roi_no==-1){
            cm.popmsg("먼저 이벤트종류를 추가하여야 합니다.");
            return;
        }
        mg.now_group_event_is_roi_edit = (mg.now_group_event_is_roi_edit ? 0 : 1);
        if(mg.now_group_event_is_roi_edit){
            $(".group_event_canvas").addClass("on");
            $("#btn_group_event_roi").text("ROI 설정 완료").addClass("btn-red");
            $("#group_event_roi_desc").show();
            $(".roi-second-btn-wrap ").show();
        } else {
            $(".group_event_canvas").removeClass("on");
            $("#btn_group_event_roi").text("ROI 설정").removeClass("btn-red");
            $("#group_event_roi_desc").hide();
            $(".roi-second-btn-wrap ").hide();
        }
    },
    group_click_select_roi:function (no) {
        mg.now_roi_no = no;
        $(".group-roi-wrap .btn-white-border").removeClass("btn-white-border");
        $("#btn_group_roi_"+no).addClass("btn-white-border");
        mg.group_event_redraw_roi();
    },
    group_click_roi_add:function () {
        if(mg.now_roi_no>=0 && mg.temp_roi[mg.now_roi_no].pnts.length<=2) {
            cm.popmsg("현재 ROI의 포인트를 더 추가해야 합니다.");
            return;
        }
        mg.now_roi_no ++;
        mg.temp_roi.push({event_kind:$("#sel_group_event_kind").val(), pnts:[] });
        mg.group_event_roi_wrap_renew();
    },
    group_click_roi_remove:function () {
        if(mg.now_roi_no==-1) return;
        if(mg.temp_roi.length>0)  mg.temp_roi.splice(mg.now_roi_no, 1);
        mg.now_roi_no = (mg.temp_roi.length==0 ? -1 : 0);
        mg.group_event_roi_wrap_renew();
    },
    group_event_onchange_kind:function () {
        let value = $("#sel_group_event_kind").val();
        let desc = "";
        mg.event_kinds.forEach(function(event_kind,  i){
            if(event_kind.name == value) desc = event_kind.desc;
        });
        $("#group_event_desc").text(desc);
    },

    group_pop_time:function () {
        if(mg.now_group_no==-1) return;
        let group=mg.info.groups[mg.now_group_no];
        if(group.process_time.length>0 && group.process_time[0].weekday==undefined) group.process_time=[];
        mg.temp= ut.clone(group);
        mg.group_pop_time_renew();
        $("#pop_group_time input[type=checkbox]").each(function(i, input){
            $(input).prop("checked", true);
        });
        $("#group_time_start").val("18:00");
        $("#group_time_end").val("09:00");
        cm.show_pop('pop_group_time');
    },
    group_pop_time_renew:function () {
        let html="";
        mg.temp.process_time.forEach(function (process, i) {
            html += '<div class="msetting-line">';
            let text="";
            process.weekday.forEach(function (week) {
                text += ut.yoil(week) + ", ";
            });
            text = text.substring(0, text.length-2);
            html += '<span class="msetting-line-item">'+text+'</span>';
            html += '<span class="msetting-line-item">'+process.start + ' ~ '+ process.end + '</span>';
            html += '<a onclick="mg.group_pop_time_click_delete('+i+')" href="javascript:;" class="btn btn-micro btn-red">삭제</a>';
            html += '</div>';
        });
        $("#msetting_line_wrap").html(html);
    },
    group_pop_time_click_add:function () {
        let f=fgroup_time;
        if($("#pop_group_time input[type=checkbox]:checked").length==0){
            cm.popmsg("먼저 추가할 요일을 선택해야 합니다.");
            return;
        }
        if(!cm.form_check(f)) return;
        let weekday=[];
        $("#pop_group_time input[type=checkbox]:checked").each(function(i, input){
            weekday.push(parseInt($(input).val()));
        });
        mg.temp.process_time.push({weekday:weekday, start:f.start.value, end:f.end.value});
        mg.group_pop_time_renew();
    },
    group_pop_time_click_delete:function (no) {
        cm.popmsg_confirm("선택한 시간을 삭제하시겠습니까?", function (no) {
            mg.temp.process_time.splice(no, 1);
            mg.group_pop_time_renew();
            cm.closepop();
            cm.toast('CAMERA DELETED');
        });
    },
    group_click_analysis:function () {
        if(mg.now_group_no==-1) return;
        bw.send_cmd('mg-group-analysis', {no:mg.now_group_no},function(){
            let group = mg.info.groups[mg.now_group_no];
            group.is_processing = (group.is_processing?0:1);
            if(group.is_processing) $("#btn_group_edit, #btn_group_event, #btn_group_time").hide();
            else $("#btn_group_edit, #btn_group_event, #btn_group_time").show();
            mg.group_next(0);
        });
    },
    group_click_record:function () {
        if(mg.now_group_no==-1) return;
        let group = mg.info.groups[mg.now_group_no];
        if(!group.is_recording && !group.is_processing) {
            cm.popmsg("먼저 해석을 시작하여야 합니다.");
            return;
        }
        bw.send_cmd('mg-group-record', {no:mg.now_group_no},function(){
            let group = mg.info.groups[mg.now_group_no];
            group.is_recording = (group.is_recording?0:1);
            mg.group_next(0);
        });
    },
    group_click_snapshot:function () {
        if(mg.now_group_no==-1) return;
        let group = mg.info.groups[mg.now_group_no];
        if(!group.is_processing) {
            cm.popmsg("먼저 해석을 시작하여야 합니다.");
            return;
        }
        bw.send_cmd('mg-group-snapshot', {no:mg.now_group_no},function(){
            cm.toast("Snapshot saved!")
        });
    },

    //endregion

    //region == RIGHT SETTING
    setting_select:function (nav) {
        $(".setting-nav-tab-menu.on").removeClass('on');
        $("#set_menu_"+nav).addClass('on');
        $(".setting-tab-contents.on").removeClass('on');
        $("#set_"+nav).addClass('on');
    },
    setting_click_search:function (page=1) {
        mg.now_search_page_no = page;
        let f = fset_search;
        let param = {
            start:f.sdate.value +' '+f.stime.value,
            end:f.edate.value +' '+f.etime.value,
            event_kind:f.event_kind.value,
            target:f.target.value,
            order:f.order.value,
            page:page,
            num_list:ut.num_list
        }
        bw.send_cmd('mg-setting-search', param,function(json){
            let html="";
            json.rows.forEach(function(row, i){
                html += '<tr>';
                html += '<td>' + row.no + '</td>';
                html += '<td>' + row.event + '</td>';
                html += '<td>' + row.camera + '</td>';
                html += '<td>' + row.target + '</td>';
                html += '<td>' + row.datetime + '</td>';
                html += '</tr>';
            });
            if(html=="") html='<tr><td colspan="5">데이터가 없습니다.</td></tr>';
            $("#set_tbody").html(html);
            $("#search_pagination").html(ut.pagination(json.total, mg.now_search_page_no, ut.num_list, "mg.setting_click_search"));
        });
    },
    setting_click_export:function () {
        let f = fset_search;
        let param = {
            start:f.sdate.value +' '+f.stime.value,
            end:f.edate.value +' '+f.etime.value,
            event_kind:f.event_kind.value,
            target:f.target.value,
            order:f.order.value,
            page:0,
            num_list:ut.num_list
        }
        bw.send_cmd('mg-setting-export', param,function(json){
            cm.toast("FILE SAVED")
        });
    },
    setting_click_remove:function () {
        cm.popmsg_confirm("저장된 내용을 삭제하시겠습니까?", function () {
            let f = fset_search;
            let param = {
                start: f.sdate.value + ' ' + f.stime.value,
                end: f.edate.value + ' ' + f.etime.value,
                event_kind: f.event_kind.value,
                target: f.target.value,
                order: f.order.value,
                page: 0,
                num_list: ut.num_list
            }
            bw.send_cmd('mg-setting-remove', param, function (json) {
                cm.closepop();
                cm.toast("FILE DELETED")
            });
        });
    },
    setting_save:function (mode) {
        let f;
        if(mode==11) { //
            f=fset_reconnect;
            mg.info.setting.reconnect.is_use = (f.is_use.checked ? 1 : 0);
            mg.info.setting.reconnect.second = parseInt(f.second.value);
            bw.send_cmd('mg-setting-reconnect', mg.info.setting.reconnect,function(){
                cm.toast('RECONNECT INFO SAVED');
            });
        }
        else if(mode==13) { //
            f=fset_folder;
            if(!cm.form_check(f)) return;
            mg.info.setting.folder.record = f.record.value;
            mg.info.setting.folder.snapshot = f.snapshot.value;
            bw.send_cmd('mg-setting-folder', mg.info.setting.folder,function(){
                cm.toast('FOLDER INFO SAVED');
            });
        }
        else if(mode==14) { //
            f=fset_privacy;
            if(!cm.form_check(f)) return;
            if(f.password.value != f.repassword.value){
                cm.popmsg("비밀번호가 서로 같지 않습니다. 확인하여 주세요.");
                return;
            }
            mg.info.setting.userid = f.userid.value;
            mg.info.setting.password = f.password.value;
            bw.send_cmd('mg-setting-privacy', mg.info.setting,function(){
                cm.toast('PRIVACY INFO SAVED');
            });
        }
    },
    setting_click_reconnect:function () {

    },
    setting_click_check_resource:function () {
        bw.send_cmd('mg-setting-resource', null,function(data){
            cm.toast('RESOURCE INFO RENEWED');
        });
    },
    setting_click_select_record_folder:function () {
        bw.send_cmd('mg-setting-record-folder', fset_folder.record.value,function(data){
            fset_folder.record.value = data;
            cm.toast('RECORD-FOLDER SELECTED');
        });
    },
    setting_click_select_snapshot_folder:function () {
        bw.send_cmd('mg-setting-snapshot-folder', fset_folder.snapshot.value,function(data){
            fset_folder.snapshot.value = data;
            cm.toast('SNAPSHOT-FOLDER SELECTED');
        });
    },
    setting_click_download_manual:function () {
        bw.send_cmd('mg-setting-manual', null,function(data){
            cm.toast('OPEN MANUAL');
        });
    },
    test:function () {

    },

    //endregion

    //region == RIGHT SERVER & ADMIN & USER
    server_save:function () {
        if(!cm.form_check(fsvr)) return;
        mg.info.server.name = fsvr.name.value;
        mg.info.server.ip = fsvr.ip.value;
        mg.info.server.port = fsvr.port.value;
        mg.info.server.userid = fsvr.userid.value;
        mg.info.server.password = fsvr.password.value;
        bw.send_cmd('mg-server-update', mg.info.server,function(){
            $("#td_svr_name").html(mg.info.server.name);
            $("#td_svr_ip").html(mg.info.server.ip);
            cm.toast('SERVER INFO SAVED');
        });
    },

    admin_select:function (nav) {
        $(".tab-content.manager .group-nav-tab-menu.on").removeClass('on');
        $("#mtab_"+nav).addClass('on');
        $(".tab-content.manager .manager-tab-contents.on").removeClass('on');
        $("#mtab_contents_"+nav).addClass('on');
    },
    admin_click_edit_move:function (direction) {
        if(direction==-1){//to out
            if($("#admin_kind_out input[type=checkbox]:checked").length==0){
                cm.popmsg("먼저 이동할 이벤트를 선택해야 합니다.");
                return;
            }
            $("#admin_kind_in input[type=checkbox]:checked").each(function(i, input){
                $(input).parent().appendTo("#admin_kind_out");
            });
        }
        else {
            if($("#admin_kind_out input[type=checkbox]:checked").length==0){
                cm.popmsg("먼저 이동할 이벤트를 선택해야 합니다.");
                return;
            }
            $("#admin_kind_out input[type=checkbox]:checked").each(function(i, input){
                $(input).parent().appendTo("#admin_kind_in");
            });
        }
    },
    admin_save:function () {
        if(!cm.form_check(fadmin)) return;
        mg.info.admin.license_cnt = fadmin.license_cnt.value;
        mg.info.admin.logo = fadmin.logo.value;
        mg.info.admin.program_name = fadmin.program_name.value;
        mg.info.admin.manual = fadmin.manual.value;
        mg.info.admin.license_kind = [];
        mg.event_kinds.forEach(function(event_kind, i){
            if($("#admin_kind_in #admin_kind_"+i).length>0){
                mg.info.admin.license_kind.push(event_kind.name);
            }
        });
        bw.send_cmd('mg-admin-update', mg.info.admin,function(){
            $("#logo").attr("src", "./images/logo.png");
            bw.send_cmd('mg-load-image',mg.info.admin.logo, function (data)
            {
                $("#logo").attr("src", data);
            });
            $("#program_name").attr("src", mg.info.admin.program_name);
            cm.toast('ADMIN INFO SAVED');
        });
    },
    admin_click_select_logo:function () {
        bw.send_cmd('mg-admin-logo', fadmin.logo.value,function(data){
            fadmin.logo.value = data;
            cm.toast('LOGO FILE SELECTED');
        });
    },
    admin_click_select_manual:function () {
        bw.send_cmd('mg-admin-manual', fadmin.manual.value,function(data){
            fadmin.manual.value = data;
            cm.toast('MANUAL FILE SELECTED');
        });
    },
    admin_click_select_firmware:function () {
        bw.send_cmd('mg-admin-firmware', fadmin.firmware.value,function(data){
            fadmin.firmware.value = data;
            cm.toast('FIRMWARE FILE SELECTED');
        });
    },
    admin_click_firmware_apply:function () {
        bw.send_cmd('mg-admin-firmware-apply', fadmin.firmware.value,function(data){
            cm.toast('FIRMWARE FILE APPLIED');
        });
    },
    user_click_change_password:function () {
        cm.show_pop("pop_user");
    },
    user_save_password:function () {
        let f = fuser;
        if(!cm.form_check(f)) return;
        if(f.password.value != f.repassword.value){
            cm.popmsg("비밀번호가 서로 같지 않습니다. 확인하여 주세요.");
            return;
        }
        let cmd='mg-password-admin';
        if(!mg.is_admin) {
            cmd='mg-password-user';
            mg.info.setting.password = f.password.value
        }
        bw.send_cmd(cmd, f.password.value,function(){
            cm.hide_pop();
            cm.toast('PASSWORD CHANGED');
        });
    },
    //endregion

    test:function () {

    },
}
if (typeof qt != 'undefined')
{
    document.addEventListener("DOMContentLoaded", function () {
        new QWebChannel(qt.webChannelTransport, function (channel) {
            bw.ch = channel.objects.backend;
        });
    });
}

//BACKEND WORKER PYQT 통신
bw={
    ch:null, is_able:true,
    init:function(){
        if(bw.ch == null) bw.is_able = false;
    },
    send_cmd:function(cmd, data, callback=null){
        let param = {cmd:cmd, data:data};
        //TODO DEV WITHOUT BACKEND
        if(bw.ch==null){
            bw.dev_respond_instead_of_be(param, callback);
            return;
        }
        if(!bw.is_able) return false;
        bw.ch.be_send_cmd(param, function(json) {
            //param & json = {cmd:"", data:{}, error:"", action:""}
            //console.log(JSON.stringify(json));
            bw._treat_return_json(json, callback);
        });
    },
    _treat_return_json:function(json, callback){
        try {
            if(json.error != ""){
                cm.popmsg(json.error);
            }
            else {
                if(callback != null) callback(json.data || {});
                else if(json.action != "") eval(json.action);
            }
        } catch(ex) {
            console.log('error', ex.message);
        }
    },
    //개발용 : 백엔드 없이 브라우져로 실행시 응답 설정
    dev_respond_instead_of_be:function(param, callback=null){
        let json = {cmd:param.cmd, data:{}, error:"", action:""};
        if(param.cmd=="mg-init"){
            json.data = {is_admin:1, userid:"dev.msvision", info : {
                    cameras:[
                        {property:{name:"카메라 1", no:"Camera 1", ip:"117.17.159.31", stream_no:"Stream 2", port:80, mac:"mac1", userid:"admin", password:"admin"},
                            roi:[{event_kind:"침입", pnts:[{x:0.540625,y:0.2005642361111111},{x:0.9302083333333333,y:0.1783420138888889},{x:0.9489583333333333,y:0.3255642361111111},{x:0.7489583333333333,y:0.8061197916666667},{x:0.5010416666666667,y:0.8116753472222222}]}], group_no:0, is_connected:1, event_kind:"침입", image:{src:"./tmp/tmp3.jpg", w:640,h:480, fps:25, datatime:"2023-05-11 12:12:14"}},
                        {property:{name:"카메라 2", no:"Camera 2", ip:"117.17.159.32", stream_no:"Stream 2", port:80, mac:"mac2", userid:"admin", password:"admin"},
                            roi:[[{x:0.640625,y:0.7033420138888888},{x:0.6427083333333333,y:0.7616753472222222},{x:0.8447916666666667,y:0.9977864583333333},{x:0.8927083333333333,y:0.9950086805555556},{x:0.8802083333333334,y:0.7672309027777777}]], group_no:0, is_connected:1, event_kind:"배회", image:{src:"./tmp/tmp1.jpg", w:640,h:480, fps:25, datatime:"2023-05-11 12:12:14"}},
                        {property:{name:"카메라 3", no:"Camera 3", ip:"117.17.159.33", stream_no:"Stream 1", port:80, mac:"mac3", userid:"admin", password:"admin"},
                            roi:[], group_no:-1, is_connected:0, event_kind:"침입", image:{src:"./tmp/tmp2.jpg", w:640,h:480, fps:25, datatime:"2023-05-11 12:12:14"}}
                    ],
                    groups:[{name:"GROUP1", is_processing:0, is_recording:0, process_time:[], grid:2, page:0}],
                    server:{name:"NVR", ip:"117.17.159.31", port:8081, userid:"admin", password:"admin"},
                    setting:{reconnect:{is_use:0, second:60}, folder:{record:"", snapshot:""}, userid:"dev.msvision", password:""},
                    admin:{license_cnt:10, license_kind:["배회"], logo:"./images/logo.png", program_name:"MS-AI1000 1.0.0.0", manual:""}
                }};
        }
        else if(param.cmd=="login"){
            location.href="manage.html";
        }
        else if(param.cmd=="mg-setting-search"){
            json.data = {};
            json.data.total = 42;
            json.data.rows = [];
            for(let i=0;i<ut.num_list;i++){
                json.data.rows.push( {no:i+1, event:'침입', camera:'Camera 1', target:'사람'+i, datetime:'2023-04-20 14:05:45'});
            }
        }
        bw._treat_return_json(json, callback);
    },
    test:function(){
    },
}

ut={
    num_list:10,
    //개체 복사(deep copy)
    clone:function (obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    yoil:function (no) {
        let han = ["일", "월", "화", "수", "목", "금", "토"];
        return han[no];
    },
    //PAGING
    pagination:function (totalpage, curpage, pagerows, target) {
        let htm = "<ul class='pagination'>";
        if (totalpage > 0) {
            if(pagerows==0) { pagerows=4;};
            let pagecount = (totalpage / pagerows) + 1;
            if (totalpage % pagerows == 0) pagecount = pagecount - 1;
            let blockpage = Math.floor((curpage - 1) / 10) * 10 + 1;

            if (blockpage == 1) htm += "<li class='front'></li>";
            else htm += "<li class='front'><a class='' href='javascript:;' onclick='" + target + "(" + (blockpage - 1) + ")'></a></li> ";
            let i = 1;
            while ((i <= 10) && (blockpage <= pagecount)) {
                if (blockpage == curpage) htm += "<li class='on'>" + blockpage + "</li>";
                else htm += "<li><a class='' href='javascript:;' onclick='" + target + "(" + blockpage + ")'>" + blockpage + "</a></li>";
                i++;
                blockpage++;
            }
            if (blockpage > pagecount) htm += "<li class='end'></li>";
            else htm += "<li class='end'><a class='' href='javascript:;' onclick='" + target + "(" + blockpage + ")'></a></li> ";
        } else {
            htm += "<li class=''>-</li>";
        }
        htm += "</ul>";
        return htm;
    },
}
