package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
)

// downloadFile baixa um arquivo de uma URL para o caminho especificado.
func downloadFile(filepath string, url string) error {
	out, err := os.Create(filepath)
	if err != nil {
		return fmt.Errorf("erro ao criar arquivo: %v", err)
	}
	defer out.Close()

	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("erro ao fazer o download: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("erro ao baixar: status %s", resp.Status)
	}

	_, err = io.Copy(out, resp.Body)
	return err
}

// showSpinner exibe um símbolo de carregamento no terminal.
func showSpinner(stopChan chan bool) {
	chars := []rune{'|', '/', '-', '\\'}
	i := 0
	for {
		select {
		case <-stopChan:
			fmt.Print("\r")
			return
		default:
			fmt.Printf("\r%c", chars[i%len(chars)])
			time.Sleep(100 * time.Millisecond)
			i++
		}
	}
}

// parsePythonVersion analisa a saída do comando `python --version`.
func parsePythonVersion(output string) (float64, error) {
	parts := strings.Fields(output)
	if len(parts) < 2 {
		return 0, fmt.Errorf("formato de versão inesperado")
	}
	versionStr := parts[1]
	versionParts := strings.Split(versionStr, ".")
	if len(versionParts) < 2 {
		return 0, fmt.Errorf("formato de versão inesperado")
	}
	majorMinor := strings.Join(versionParts[:2], ".")
	version, err := strconv.ParseFloat(majorMinor, 64)
	if err != nil {
		return 0, fmt.Errorf("erro ao converter versão: %v", err)
	}
	return version, nil
}

// installPython instala o Python a partir do caminho do instalador.
func installPython(installerPath string) error {
	absPath, err := filepath.Abs(installerPath)
	if err != nil {
		return fmt.Errorf("erro ao obter o caminho absoluto do instalador: %v", err)
	}

	fmt.Println("Instalando Python...")
	stopChan := make(chan bool)
	go showSpinner(stopChan)

	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command(absPath, "/quiet", "InstallAllUsers=1", "PrependPath=1")
	case "linux", "darwin":
		cmd = exec.Command("sh", "-c", fmt.Sprintf(
			"tar -xzf %s && cd Python-3.10.0 && ./configure && make && sudo make install",
			installerPath,
		))
	default:
		stopChan <- true
		return fmt.Errorf("sistema operacional não suportado")
	}

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		stopChan <- true
		return fmt.Errorf("erro ao instalar Python: %v", err)
	}

	stopChan <- true
	fmt.Print("\r")
	fmt.Println("Instalação do Python concluída com sucesso!")
	return nil
}

// checkPythonVersion verifica a versão do Python instalado.
func checkPythonVersion(pythonCmd string, requiredVersion float64) (bool, error) {
	cmd := exec.Command(pythonCmd, "--version")
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	err := cmd.Run()
	if err != nil {
		return false, err
	}
	output := out.String()
	installedVersion, err := parsePythonVersion(output)
	if err != nil {
		return false, err
	}
	if installedVersion >= requiredVersion {
		fmt.Printf("Python versão %.2f já está instalado.\n", installedVersion)
		return true, nil
	}
	return false, nil
}

// executePythonScript executa um script Python.
func executePythonScript(pythonCmd string, scriptPath string) error {
	cmd := exec.Command(pythonCmd, scriptPath)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("erro ao executar o assistente: %v", err)
	}
	return nil
}

func main() {
	requiredVersion := 3.10
	scriptPath := "Assistente/main.py"
	pythonCmds := []string{"python3", "python"}

	var pythonCmd string
	pythonInstalled := false
	var err error

	// Verifica se alguma versão do Python está instalada.
	for _, cmd := range pythonCmds {
		pythonInstalled, err = checkPythonVersion(cmd, requiredVersion)
		if pythonInstalled {
			pythonCmd = cmd
			break
		}
	}

	if pythonInstalled {
		// Executa o script Python.
		if err := executePythonScript(pythonCmd, scriptPath); err != nil {
			fmt.Println(err)
		}
		return
	}

	// Se não estiver instalado, procede com a instalação.
	var downloadURL, installerPath string
	switch runtime.GOOS {
	case "windows":
		downloadURL = "https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe"
		installerPath = "python-3.10.0-amd64.exe"
	case "linux", "darwin":
		downloadURL = "https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz"
		installerPath = "Python-3.10.0.tgz"
	default:
		fmt.Println("Sistema operacional não suportado.")
		return
	}

	fmt.Println("Baixando o instalador do Python...")
	stopChan := make(chan bool)
	go showSpinner(stopChan)

	if err := downloadFile(installerPath, downloadURL); err != nil {
		stopChan <- true
		fmt.Printf("Erro ao baixar o instalador: %v\n", err)
		return
	}
	stopChan <- true
	defer os.Remove(installerPath)

	if err := installPython(installerPath); err != nil {
		fmt.Printf("Erro durante a instalação: %v\n", err)
		return
	}

	// Verifica a versão do Python instalado.
	for _, cmd := range pythonCmds {
		pythonInstalled, err = checkPythonVersion(cmd, requiredVersion)
		if pythonInstalled {
			pythonCmd = cmd
			break
		}
	}

	if !pythonInstalled {
		fmt.Printf("Erro ao verificar a versão do Python após a instalação: %v\n", err)
		return
	}

	// Executa o script Python.
	if err := executePythonScript(pythonCmd, scriptPath); err != nil {
		fmt.Println(err)
	}
}
