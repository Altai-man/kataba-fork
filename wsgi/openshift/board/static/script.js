function temp_look(is_nsfw,selector) {

    if (is_nsfw) {
        selector.mouseenter(function() {
            $(this).css('opacity','1.0');
        });
        
        selector.mouseleave(function() {
            $(this).css('opacity','0');
        });
    } else
        selector.unbind();
        
}

function show_linked(selector) {
    var original_selector = selector;
    selector.hover(
        function() {
            var csrftoken = $.cookie('csrftoken');
            var cont = $(this).children('div.post_quote');
            var link_to = $(this).children('a.link_to_post').html().slice(8);
            var type = '';
            
            if (link_to[0] == 't')
                type = 'thread';
            else
                type = 'post';
            
            var id = parseInt(link_to.slice(1));
            
            var url = '/'+type+'/get/'+id+'/';
            
            if (!cont.html().length) {
                $.ajax({
                    type:'GET',
                    crossDomain: false,
                    cache: true,
                    url: url,
                    data: {},
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    },
                    statusCode: {
                        404: function() {
                            cont.html('NOT FOUND (404)')
                        }
                    },
                    success: function(output) {
                        cont.html(output.answer);
                        selector = $(selector.selector); // Updating selector because new posts can contain new links.
                        
                        // Warning! Recursive call!
                        if (selector.length != original_selector.length) {
                            original_selector.unbind();
                            selector = show_linked(selector);
                        }
                    },
                });
            }
            
            cont.fadeIn();
        },
        function() {
            var cont = $(this).children('div.post_quote');
            cont.fadeOut();
        }
    
    );
    return selector;
}
    
$(document).ready(function() {
    // Hide/show left upper menu
    $('#switch').click(function() {
        var swtch = $('#switch').html();
        if (swtch == '&lt;') {
            $('#header_content').hide();
            $('#switch').html('&gt;');
        } else {
            $('#header_content').show();
            $('#switch').html('&lt;');
        }
    });
    
    // NSFW option and it's cookies
    if ($.cookie('nsfw') == 'true') {
        var selector = $('img.post_img');
        selector.css('opacity','0');
        $('#nsfw').attr('checked',true);
        temp_look(true,selector);
    }
    
    $('#nsfw').change(function() {
        var nsfw = $('#nsfw').is(':checked');
        var selector = $('img.post_img');
        if (nsfw) {
            selector.css('opacity','0');
            $.cookie('nsfw',true,{path: '/'});
            temp_look(true,selector);
        }
        else {
            selector.css('opacity','1.0');
            $.cookie('nsfw',false,{path: '/'});
            temp_look(false,selector);
        }
    });
    
    // Create thread via form
    $('#send_thread').click(function() {
        var csrftoken = $.cookie('csrftoken');
        var board_name = $('#board_name').val()
        var form = new FormData(document.getElementById('send_form'));
        
        $.ajax({
            type:'POST',
            crossDomain: false,
            processData: false,
            cache: false,
            contentType: false,
            MimeType: 'multipart/form-data',
            url: "/"+board_name+"/add_thread",
            data: form,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function(output) {
                if (output.success == true) {
                    document.location.href = output.url
                } else {
                    $('#form_table').html(output.form)
                }
                //$('#form_table').html(output.form);
            },
        });
    });

    // Send post via ajax
    $('#send_post').click(function() {
        var csrftoken = $.cookie('csrftoken');
        var thread_id = $('#thread_id').val();
        var board_name =  $('#board_name').val();
        var form = new FormData(document.getElementById('send_form'));
        
        $.ajax({
            type:'POST',
            crossDomain: false,
            processData: false,
            cache: false,
            contentType: false,
            MimeType: 'multipart/form-data',
            url: "/"+board_name+"/thread/"+thread_id+'/add_post',
            data: form,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function(output) {
                if (output.success == true) {
                    $('#refresh').click();
                }
                $('#form_table').html(output.form);
            },
        });
    });
    
    // Enabling pages
    $('#pages div').click(function() {
        document.location.href='/'+$(this).attr('data-name');
    });

    // Full image by click
    $('img.post_img').click(function() {
        var temp = '';
        temp = $(this).attr('src');
        $(this).attr('src',$(this).attr('data-alt_name'));
        $(this).attr('data-alt_name',temp);
    });
    
    // Link to post/thread
    $('span.post_link').click(function() {
        var text_field = $('#id_text');
        if (text_field.length)
            text_field.val(text_field.val()+'>>'+$(this).html().slice(1));
    });
    
    // to the start
    $('#up').click(function() {
        document.location.href = window.location.pathname+'#';
    });
    
    // AJAX request for new posts in thread
    $('#refresh').click(function() {
        var csrftoken = $.cookie('csrftoken');
        var thread_id = $('#thread_id').val();
        var board_name =  $('#board_name').val();
        var posts_numb = $('#post_cont div.post').length;
        $.ajax({
            type:'GET',
            crossDomain: false,
            cache: false,
            url: "/"+board_name+"/thread/update/"+thread_id+'/'+posts_numb,
            data: {},
            beforeSend: function(xhr) {
                $('#answer').html('Загружаем...');
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function(output) {
                if (output.is_new) {
                    // Fast, but old version without animation.
//                   $('#post_cont').html($('#post_cont').html()+output.new_threads);

                    // Animated version
                    var content = "<div class='inv_cont'>"+output.new_threads+"</div>"
                    $('#post_cont').html($('#post_cont').html()+content);
                    $('#post_cont div.inv_cont').last().fadeIn(700)

                    $('#answer').html('');
                    
                    // move to the page's end
                    var url = location.href;
                    location.href = "#bottom_cont";
                    history.replaceState(null,null,url);
                    
                    // make NSFW new pics
                    $('#nsfw').change()

                    // Links
                    window.links = $('div.link_to_content')
                    window.links = show_linked(window.links)
                }
                else
                    $('#answer').html('Новых постов нет!');
            },
        });
    });
    
    // Show/hide post form and it's cookie
    $('#form_switch').click(function() {
        if ($.cookie('form') == 'false') {
            $.cookie('form',true,{path: '/'});
            
        }
        else {  
            $.cookie('form',false,{path: '/'});
        }
        $('#form_cont').slideToggle();
    });
    
    if ($.cookie('form') == 'true')
        $('#form_cont').show();

    // Show/hide options
    $('#options_button').click(function() {
        $('#options').slideToggle();
    });
    
    // Show/hide quoted posts/threads
    window.links = $('div.link_to_content')
    window.links = show_linked(window.links);

    $('#send_search').click(function() {
        var search_board = $('#search_board').val();
        var search_type = $('#search_type').val();
        var search_place = $('#search_place').val();
        var search_text = $('#search_text').val();
        
        if (search_text.length >= 3)
            document.location.href='/search/'+search_board+'/'+search_type+'/'+search_place+'/'+search_text;
        else
            alert('Запрос слишком короткий!');
    });
});
