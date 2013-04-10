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

function make_poem_boxes(ps) {
    var L = []
    $.each(ps, function(i, p) {
        L.push('<div class="item"><div class="item-header"></div><div class="item-body"><p>');
        L.push(p.name);
        L.push('</p><p>');
        L.push(p.content);
        L.push('</p></div><div class="item-footer"></div></div>');
    });
    return L.join('');
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
    $('#poems').masonry({
        itemSelector : '.item',
        columnWidth : 166,
        gutterWidth: 30,
        isResizable: false,
    });
});
