# Mise a jour de Home.py — Charger l'organisation au login

## 1. Ajouter l'import en haut du fichier

Trouvez la ligne :
```python
from utils.payments import get_payment_link
```

Ajoutez juste apres :
```python
from utils.org import get_organization
```

---

## 2. Mettre a jour le handler de connexion (onglet Connexion)

Trouvez ce bloc dans la partie LOGIN :
```python
if st.button("Se connecter", use_container_width=True, key="btn_login"):
    if not l_user or not l_pwd:
        st.error("Veuillez renseigner tous les champs.")
    else:
        user, error = auth_user(l_user, l_pwd)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["username"]      = user["username"]
            st.session_state["display_name"]  = user.get("display_name", l_user.title())
            st.session_state["plan"]          = user.get("plan", "basic")
            st.session_state["email"]         = user.get("email", "")
            st.switch_page("pages/1_Dashboard.py")
        else:
            st.error(error)
```

Remplacez par :
```python
if st.button("Se connecter", use_container_width=True, key="btn_login"):
    if not l_user or not l_pwd:
        st.error("Veuillez renseigner tous les champs.")
    else:
        user, error = auth_user(l_user, l_pwd)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["username"]      = user["username"]
            st.session_state["display_name"]  = user.get("display_name", l_user.title())
            st.session_state["plan"]          = user.get("plan", "basic")
            st.session_state["email"]         = user.get("email", "")
            st.session_state["role"]          = user.get("role", "member")

            # Charger l'organisation si l'utilisateur en fait partie
            org_id = user.get("org_id")
            if org_id:
                st.session_state["org"] = get_organization(org_id)
            else:
                st.session_state["org"] = None

            st.switch_page("pages/1_Dashboard.py")
        else:
            st.error(error)
```

---

## 3. (Optionnel) Mettre a jour le handler d'inscription

Dans le bloc creation de compte basic/premium, ajoutez aussi :
```python
st.session_state["role"] = "member"
st.session_state["org"]  = None
```
juste apres la ligne `st.session_state["email"] = r_email.lower()`.

---

## 4. Tester

Apres avoir cree une organisation via la page **Admin ABIDSON**, connectez-vous
avec le compte admin genere. Vous devriez voir dans la sidebar :

```
[Nom utilisateur]
[email]
[Nom Organisation] · Premium ⭐
Administrateur d'equipe
```

Et acceder a la page **Gestion d'equipe** pour ajouter des collaborateurs.
