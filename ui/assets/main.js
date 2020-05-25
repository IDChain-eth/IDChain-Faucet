const deepLinkPrefix = 'brightid://link-verification/http:%2f%2ftest.brightid.org/idchain/';

$(function () {
  $('#connect-button').on('click', async () => {
    //Will Start the metamask extension
    const accounts = await ethereum.enable();
    const account = accounts[0];
    $('#connect-button').hide();
    new QRCode(document.getElementById("qrcode"), {
      text: deepLinkPrefix+account,
      width: 220,
      height: 220,
    });
  })
});