function format_poem(content, shortBreak) {
    content = content.replace(/。/g, '。\n').replace(/！/g, '！\n').replace(/”/g, '”\n');
    if (shortBreak) {
        content = content.replace(/，/g, '，\n');
    }
    var ps = []
    $.each(content.split('\n'), function(i, s) {
        ps.push('<p>' + s + '</p>');
    });
    return ps.join('');
}

function split_content(content, max) {
    content = content.replace(/。/g, '。\n').replace(/！/g, '！\n').replace(/”/g, '”\n');
    var ps = [];
    $.each(content.split('\n'), function(i, s) {
        if (s.length<=8) {
            ps.push('<p>' + s + '</p>');
        }
        else {
            ss = s.split('，');
            for (var i=0; i<ss.length; i++) {
                ps.push('<p>' + ss[i] + '</p>');
            }
        }
    });
    if (max > 0 && ps.length > max) {
        return ps.slice(0, max).join('') + '<p>……</p>';
    }
    return ps.join('');
}

function make_poem_boxes(ps) {
    var L = []
    $.each(ps, function(i, p) {
        L.push('<div class="item"><div class="item-header"></div><div class="item-body"><p>');
        L.push('<a href="/poem/' + p.id + '">' + p.name + '</a>');
        L.push('</p><p>');
        L.push('<a href="/poet/' + p.poet_id + '">' + p.poet_name + '</a>');
        L.push('</p>');
        L.push(split_content(p.content, 8));
        L.push('</div><div class="item-footer"></div></div>');
    });
    return L.join('');
}

function search(q) {
    L = [];
    if ($('#search .condition-dynasty').length) {
        L.push('dynasty_id=' + $('#search .condition-dynasty span.selected').attr('v'));
    }
    else if ($('#search .condition-poet').length) {
        L.push('poet_id=' + $('#search .condition-poet span.selected').attr('v'));
        L.push('poet_option=' + $('#search .condition-poet span.poet').attr('v'));
    }
    if ($('#search .condition-form').length) {
        L.push('form=' + $('#search .condition-form span.selected').attr('v'));
    }
    location.assign('/s?' + L.join('&') + '&q=' + encodeURIComponent($('#search input.search').val()));
}

$(function() {
    $(window).scroll(function() {
        if ($(window).scrollTop() > screen.height * 2) {
            $('div.go-top').show();
        }
        else {
            $('div.go-top').hide();
        }
    });
    $('div.go-top').click(function() {
        $('html, body').animate({scrollTop: 0}, 1000);
    });
    $('div.condition span').click(function() {
        $(this).parent().children('.selected').removeClass('selected');
        $(this).addClass('selected');
    });
    $('a.bigbang').click(function() {
        $('body>div').fadeOut(1000);
        var img = $('body').css('background-image');
        $('body').css('background-color', '#eddec2').css('background-image', 'none').append('<div style="width:694px;text-align:center;margin:20px auto;"><a href="javascript:location.reload()">╮（╯◇╰）╭ 中华诗词 ╮（╯◇╰）╭</a></div><div style="background-image:' + img + ';width:694px;height:1000px;border:1px solid #a38a54;margin:20px auto 20px auto;"></div>');
    });
    // pinterest styling:
    $('#poems').masonry({
        itemSelector : '.item',
        columnWidth : 166,
        gutterWidth: 30,
        isResizable: false,
    });
    // search:
    $('#search').submit(function() {
        var q = $.trim($('#search input.search').val());
        search(q);
        return false;
    });
});
