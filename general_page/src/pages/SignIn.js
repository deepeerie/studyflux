import React, { useState } from "react";
import { connect } from 'react-redux'
import Wrapper from "../layouts/Wrapper";
import { setAuth, setUser, setLoading } from "../actions";
import fetch from "../components/functions/fetchWithTimeOut";
import { Redirect } from "react-router-dom";
import AlertText from "../components/Alert/AlertText";
import { csrf_token } from "../components/vars";
import '../styles/login_style.css'

function SignIn({setAuth, setUser}) {
    const [state, setState] = useState({
        login: '',
        password: '',
        auth: false,
        alert: {not_empty: false}
    })

    const loginChange = (e) => setState((prev) => ({...prev, login: e.target.value})),
        passwordChange = (e) => setState((prev) => ({...prev, password: e.target.value}))

    const handleSubmit = () => {
        setLoading(true)

        fetch('login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrf_token
            },
            body: 'user=' + encodeURIComponent(JSON.stringify(state))
        })
            .then(response => response.json())
            .then(response => {
                if (!response.error) {
                    setUser(response.user)
                    setAuth(true)
                    setState((prev) => ({...prev, auth: true}))
                } else {
                    setState((prev) => ({...prev, alert: {
                        not_empty: true,
                        type: 'alert-danger',
                        message: response.description
                    }}))

                    setTimeout(() => setState((prev) => ({
                        ...prev,
                        alert: {not_empty: false}
                    })), 2000)
                }

                setLoading(false)
            })
            .catch(err => {
                setLoading(false)
                setState((prev) => ({...prev, alert: {
                    not_empty: true,
                    type: 'alert-danger',
                    message: 'An error occured, please try later'
                }}))
            })
    }

    if (state.auth) return <Redirect push to="/" />

    const form =
        <>
            <div className="wrapper fade_in_down">
                <div id="auth_form">
                    {state.alert.not_empty && <AlertText message={state.alert.message} className={`alert ${state.alert.type} mt-1 mb-2`} />}
                    <div>
                        <input type="text" name="username" autoFocus="" id="login" className="fade_in second mt-5"
                               placeholder="login" autoCapitalize="none" autoComplete="username" onChange={e => loginChange(e)} />
                        <input type="password" name="password" autoComplete="current-password" id="password"
                               className="fade_in third" placeholder="password" onChange={e => passwordChange(e)} />
                        <input type="submit" className="fade_in fourth" value="Log In" onClick={(e) => handleSubmit()}/>
                    </div>
                    <div id="auth_form_footer">
                        <a className="under_line_hover" href="#">Forgot Password?</a>
                    </div>
                </div>
            </div>
        </>

    return <Wrapper component={form} />
}

const mapStateToProps = store => {
    return {
        auth: store.auth,
        user: store.user,
    }
}

const mapDispatchToProps = dispatch => {
    return {
        setUser: user => dispatch(setUser(user)),
        setAuth: auth => dispatch(setAuth(auth)),
        setLoading: loading => dispatch(setLoading(loading))
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(SignIn)
