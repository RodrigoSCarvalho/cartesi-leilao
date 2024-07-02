// SPDX-License-Identifier: MIT
pragma solidity >=0.6.0 <0.9.0;

contract Leilao {
    address public beneficiario;
    uint public valorMinimoLance;
    uint public tempoTotalLeilao;
    uint public horaInicioLeilao;
    uint public maiorLance;
    address public maiorLanceVencedor;

    event LanceVencedor(address indexed vencedor, uint valor);

    constructor(address _beneficiario, uint _valorMinimoLance, uint _tempoTotalLeilao) {
        beneficiario = _beneficiario;
        valorMinimoLance = _valorMinimoLance;
        tempoTotalLeilao = _tempoTotalLeilao;
        horaInicioLeilao = block.timestamp;
    }

    function enviarLance(uint lance) external {
        require(block.timestamp < horaInicioLeilao + tempoTotalLeilao, "Leilao encerrado");
        require(lance > maiorLance, "Valor do lance nao e maior que o lance atual");

        maiorLance = lance;
        maiorLanceVencedor = msg.sender;
    }

    function encerrarLeilao() external {
        require(block.timestamp >= horaInicioLeilao + tempoTotalLeilao, "Leilao ainda nao encerrado");

        // Transferir o saldo para o beneficiário
        payable(beneficiario).transfer(address(this).balance);
        emit LanceVencedor(maiorLanceVencedor, maiorLance);
    }
}
