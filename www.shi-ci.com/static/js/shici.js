$(function() {
    $(window).scroll(function() {
        if ($(window).scrollTop() > 500) {
            $('div.go-top').show();
        }
        else {
            $('div.go-top').hide();
        }
    });
    $('div.go-top').click(function() {
        $('html, body').animate({scrollTop: 0}, 1000);
    });
    $('a.bigbang').click(function() {
        $('body>div').fadeOut(1000);
        var img = $('body').css('background-image');
        $('body').css('background-color', '#eddec2').css('background-image', 'none').append('<div style="width:694px;text-align:center;margin:20px auto;"><a href="javascript:location.reload()">╮（╯◇╰）╭ 中华诗词 ╮（╯◇╰）╭</a></div><div style="background-image:' + img + ';width:694px;height:1000px;border:1px solid #a38a54;margin:20px auto 20px auto;"></div>');
    });
});
