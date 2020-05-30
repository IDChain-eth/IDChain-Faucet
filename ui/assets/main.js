const deepLinkPrefix = 'brightid://link-verification/http:%2f%2fnode.brightid.org/idchain/';
const claimURL = './api/claim';

$(function () {
  $('#connect-button').on('click', async () => {
    //Will Start the metamask extension
    const accounts = await ethereum.enable();
    const account = accounts[0];
    $('#connect-button').hide();
    $('#qrcode').html('');
    $('#qrcode').show();
    new QRCode(document.getElementById("qrcode"), {
      text: deepLinkPrefix+account,
      width: 220,
      height: 220,
    });
    $.post({
      url: claimURL,
      data: JSON.stringify({addr: account}),
      dataType: 'json',
      contentType: 'application/json; charset=utf-8'
    });
    setTimeout(function(){
      $('#connect-button').show();
      $('#qrcode').hide();
    }, 120000);
  });
});