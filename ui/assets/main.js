const deepLinkPrefix = 'brightid://link-verification/http:%2f%2fnode.brightid.org/idchain/';
const claimURL = './api/claim';
let lastAddress;

$(function () {
  $('#ethereum-address').on('change keyup', (e) => {
    const account = $('#ethereum-address').val();
    if (account == lastAddress) {
      return;
    }
    lastAddress = account;
    $('#deeplink').attr("href", "#");
    $('#qrcode').html('');
    if (!(/^(0x){1}[0-9a-fA-F]{40}$/i.test(account))) {
      return $('#ethereum-address')[0].setCustomValidity("Invalid address");
    }
    $('#ethereum-address')[0].setCustomValidity("");
    $('#qrcode').show();
    new QRCode(document.getElementById("qrcode"), {
      text: deepLinkPrefix+account,
      width: 220,
      height: 220,
    });
    $('#deeplink').attr("href", deepLinkPrefix+account);
    $.post({
      url: claimURL,
      data: JSON.stringify({addr: account}),
      dataType: 'json',
      contentType: 'application/json; charset=utf-8',
      success: function (data) {
        if (data.error) {
          alert(data.error);
        }
      },
    });
    setTimeout(function(){
      $('#qrcode').hide();
    }, 120000);
  });
  $('#load-address-button').on('click', async () => {
    if (!window.ethereum) {
      return alert('Metamask is not installed on this browser!');
    }
    try {
      var accounts = await ethereum.enable();
    } catch (e) {
      return alert(e.message);
    }

    const account = accounts[0];
    $('#ethereum-address').val(account).trigger('change');
  });
  $('#add-network-button').on('click', async () => {
    if (!window.ethereum) {
      return alert('Metamask is not installed on this browser!');
    }
    ethereum
      .request({
        method: 'wallet_addEthereumChain',
        params: [{
        chainId: '0x4a',
        chainName: 'IDChain',
        nativeCurrency: {
          name: 'Eidi',
          symbol: 'Eidi',
          decimals: 18,
        },
        rpcUrls: ['https://idchain.one/rpc/'],
        blockExplorerUrls: ['https://explorer.idchain.one'],
        iconUrls: ['https://apps.brightid.org/logos/idchain.png']
      }]
    })
    .then((args) => console.log(args))
    .catch((error) => {
      if (error.code === 4001) {
        alert('Please connect to MetaMask.');
      } else {
        console.error(error);
      }
    });
  });
});