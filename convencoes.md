# 📌 Convenções de Commit

Este projeto segue o padrão inspirado em **Conventional Commits** para manter o histórico mais organizado e fácil de entender.

## 🔑 Estrutura


- **tipo** → Define a categoria da mudança (feat, fix, docs...).
- **escopo (opcional)** → Especifica em qual parte do projeto ocorreu a mudança.
- **descrição** → Resumo curto e objetivo da alteração.

---

## 🚀 Tipos de Commit

- **feat:** Adição de uma nova funcionalidade.  
  Ex: `feat(auth): implementar autenticação com JWT`

- **fix:** Correção de bug.  
  Ex: `fix(api): corrigir retorno da rota /users`

- **docs:** Alterações na documentação (README, Wiki, comentários no código).  
  Ex: `docs(readme): atualizar instruções de instalação`

- **style:** Mudanças que **não afetam a lógica** do código (espaços, formatação, vírgulas, aspas).  
  Ex: `style: padronizar indentação`

- **refactor:** Refatoração de código sem alterar funcionalidade.  
  Ex: `refactor(login): simplificar validação de usuário`

- **test:** Adição ou modificação de testes automatizados.  
  Ex: `test: adicionar teste unitário para cálculo de juros`

- **chore:** Tarefas de manutenção que não impactam diretamente o usuário final (configs, dependências).  
  Ex: `chore: atualizar dependências do eslint`

- **perf:** Alterações focadas em desempenho.  
  Ex: `perf: otimizar consulta ao banco de dados`

- **build:** Mudanças no processo de build ou dependências externas.  
  Ex: `build: atualizar webpack para versão 5`

- **ci:** Alterações em pipelines de integração contínua (GitHub Actions, Jenkins, etc).  
  Ex: `ci: corrigir workflow de deploy`

- **revert:** Reversão de commit anterior.  
  Ex: `revert: desfazer alteração no login`

---

## 📖 Boas práticas

1. Use frases curtas e diretas.  
   ✅ `fix: corrigir bug no cadastro de clientes`  
   ❌ `corrigi o bug que não deixava cadastrar clientes porque estava dando erro`

2. Escreva em **português ou inglês**, mas mantenha um padrão no projeto.  

3. Commits pequenos são mais fáceis de entender e revisar do que commits grandes que misturam várias coisas.

---

## 📚 Exemplos práticos

- feat(dashboard): adicionar gráfico de desempenho semanal
- fix(api): corrigir erro 500 ao buscar pacientes
- docs: atualizar README com instruções de instalação
- style: ajustar indentação de arquivos CSS
- refactor(auth): remover código duplicado
- test: adicionar teste de integração para rota /login
- chore: atualizar dependências do projeto
